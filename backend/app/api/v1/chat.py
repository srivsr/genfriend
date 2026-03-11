from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from uuid import UUID, uuid4
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging
import asyncio
from app.schemas.responses import APIResponse
from app.mentor import mentor_engine
from app.dependencies import get_current_user_id
from app.core.database import get_db
from app.models.conversation import Conversation, Message
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None


@router.post("")
async def chat(
    request: ChatRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Process a chat message with proper transaction handling.

    Transaction Strategy:
    1. Core DB operations (conversation, messages) in single transaction
    2. AI generation happens before final commit (fail-fast)
    3. Embeddings are non-critical - done async after commit
    4. Rollback on any failure before commit
    """
    conversation_id = request.conversation_id
    user_message_id = str(uuid4())
    assistant_message_id = str(uuid4())
    is_new_conversation = False

    try:
        # Phase 1: Validate/Create conversation (no commit yet)
        if not conversation_id:
            is_new_conversation = True
            conversation = Conversation(
                id=str(uuid4()),
                user_id=str(user_id),
                title=request.message[:50] + "..." if len(request.message) > 50 else request.message
            )
            db.add(conversation)
            conversation_id = UUID(conversation.id)
        else:
            # SECURITY FIX: Verify conversation belongs to current user
            result = await db.execute(
                select(Conversation).where(
                    Conversation.id == str(conversation_id),
                    Conversation.user_id == str(user_id)  # IDOR protection
                )
            )
            conversation = result.scalar_one_or_none()
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")

        # Phase 2: Create user message (no commit yet)
        user_message = Message(
            id=user_message_id,
            conversation_id=str(conversation_id),
            role="user",
            content=request.message
        )
        db.add(user_message)

        # Phase 3: Generate AI response BEFORE committing
        # This is the most likely failure point - fail fast before persisting
        try:
            response = await mentor_engine.process(str(user_id), request.message, "app")
        except Exception as e:
            logger.error(f"Mentor engine failed for user {user_id}: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=503,
                detail="AI service temporarily unavailable. Please try again."
            )

        # Phase 4: Create assistant message (no commit yet)
        assistant_message = Message(
            id=assistant_message_id,
            conversation_id=str(conversation_id),
            role="mentor",
            content=response.content,
            intent=response.context_used.get("intent") if response.context_used else None
        )
        db.add(assistant_message)

        # Phase 5: Single atomic commit for all DB operations
        await db.commit()

    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        # Rollback on any unexpected error
        logger.error(f"Chat transaction failed for user {user_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to process message")

    # Phase 6: Embeddings - non-critical, done after successful commit
    # These run async and don't block the response
    # Failures are logged but don't affect the user experience
    asyncio.create_task(
        _embed_messages_background(
            db=db,
            user_id=str(user_id),
            conversation_id=str(conversation_id),
            user_message_id=user_message_id,
            user_content=request.message,
            assistant_message_id=assistant_message_id,
            assistant_content=response.content
        )
    )

    return APIResponse(data={
        "message": {
            "id": assistant_message.id,
            "role": "mentor",
            "content": response.content,
            "context_used": response.context_used,
            "created_at": datetime.utcnow()
        },
        "conversation_id": conversation_id
    })


async def _embed_messages_background(
    db: AsyncSession,
    user_id: str,
    conversation_id: str,
    user_message_id: str,
    user_content: str,
    assistant_message_id: str,
    assistant_content: str
):
    """
    Background task to create embeddings for messages.
    Non-critical - failures are logged but don't affect the chat.
    """
    try:
        # Need a fresh session for background task
        from app.core.database import async_session
        async with async_session() as bg_db:
            embedding_service = EmbeddingService(bg_db)

            # Embed user message
            try:
                await embedding_service.embed_conversation(
                    user_id=user_id,
                    message_id=user_message_id,
                    content=user_content,
                    role="user",
                    session_id=conversation_id
                )
            except Exception as e:
                logger.warning(f"Failed to embed user message {user_message_id}: {e}")

            # Embed assistant message
            try:
                await embedding_service.embed_conversation(
                    user_id=user_id,
                    message_id=assistant_message_id,
                    content=assistant_content,
                    role="mentor",
                    session_id=conversation_id
                )
            except Exception as e:
                logger.warning(f"Failed to embed assistant message {assistant_message_id}: {e}")

    except Exception as e:
        logger.error(f"Background embedding task failed: {e}")


@router.get("/history")
async def get_history(
    conversation_id: Optional[UUID] = None,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    if conversation_id:
        # SECURITY FIX: Join to Conversation and verify user ownership
        result = await db.execute(
            select(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(
                Message.conversation_id == str(conversation_id),
                Conversation.user_id == str(user_id)  # IDOR protection
            )
            .order_by(Message.created_at.asc())
        )
        messages = list(result.scalars().all())
    else:
        result = await db.execute(
            select(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == str(user_id))
            .order_by(Message.created_at.desc())
            .limit(50)
        )
        messages = list(result.scalars().all())
        messages.reverse()

    return APIResponse(data=[
        {
            "id": m.id,
            "conversation_id": m.conversation_id,
            "role": m.role,
            "content": m.content,
            "intent": m.intent,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in messages
    ])


@router.get("/conversations")
async def get_conversations(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == str(user_id))
        .order_by(desc(Conversation.updated_at))
        .limit(20)
    )
    conversations = list(result.scalars().all())

    return APIResponse(data=[
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        }
        for c in conversations
    ])


@router.get("/conversation/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == str(conversation_id), Conversation.user_id == str(user_id))
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == str(conversation_id))
        .order_by(Message.created_at.asc())
    )
    messages = list(messages_result.scalars().all())

    return APIResponse(data={
        "conversation": {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None
        },
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "intent": m.intent,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in messages
        ]
    })
