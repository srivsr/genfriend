from typing import List, Optional
from openai import AsyncOpenAI
from app.config import settings
from app.repositories.embedding_repository import EmbeddingRepository
from sqlalchemy.ext.asyncio import AsyncSession


class EmbeddingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = EmbeddingRepository(db)
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.model = settings.embedding_model
        self.dimension = settings.embedding_dimension

    async def create_embedding(self, text: str) -> List[float]:
        if not self.client:
            return [0.0] * self.dimension

        response = await self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

    async def embed_and_store(
        self,
        user_id: str,
        content: str,
        source_type: str,
        source_id: str,
        metadata: dict = None
    ) -> str:
        embedding = await self.create_embedding(content)
        result = await self.repo.store(
            user_id=user_id,
            content=content,
            source_type=source_type,
            source_id=source_id,
            embedding=embedding,
            metadata=metadata
        )
        return result.id

    async def search(
        self,
        user_id: str,
        query: str,
        source_types: List[str] = None,
        top_k: int = 10
    ) -> List[dict]:
        query_embedding = await self.create_embedding(query)
        return await self.repo.vector_search(
            user_id=user_id,
            query_embedding=query_embedding,
            source_types=source_types,
            top_k=top_k
        )

    async def delete_source(self, source_id: str) -> bool:
        return await self.repo.delete_by_source(source_id)

    async def embed_journal_entry(
        self,
        user_id: str,
        entry_id: str,
        content: str,
        entry_type: str,
        mood: str = None
    ) -> str:
        metadata = {"entry_type": entry_type, "mood": mood}
        return await self.embed_and_store(
            user_id=user_id,
            content=content,
            source_type="journal",
            source_id=entry_id,
            metadata=metadata
        )

    async def embed_goal(
        self,
        user_id: str,
        goal_id: str,
        title: str,
        description: str,
        why: str = None
    ) -> str:
        full_content = f"{title}. {description}"
        if why:
            full_content += f" Why: {why}"
        metadata = {"title": title}
        return await self.embed_and_store(
            user_id=user_id,
            content=full_content,
            source_type="goal",
            source_id=goal_id,
            metadata=metadata
        )

    async def embed_task(
        self,
        user_id: str,
        task_id: str,
        title: str,
        description: str = None,
        outcome_notes: str = None
    ) -> str:
        parts = [title]
        if description:
            parts.append(description)
        if outcome_notes:
            parts.append(f"Outcome: {outcome_notes}")
        full_content = ". ".join(parts)
        metadata = {"title": title, "has_outcome": bool(outcome_notes)}
        return await self.embed_and_store(
            user_id=user_id,
            content=full_content,
            source_type="task",
            source_id=task_id,
            metadata=metadata
        )

    async def embed_conversation(
        self,
        user_id: str,
        message_id: str,
        content: str,
        role: str,
        session_id: str = None
    ) -> str:
        metadata = {"role": role, "session_id": session_id}
        return await self.embed_and_store(
            user_id=user_id,
            content=content,
            source_type="conversation",
            source_id=message_id,
            metadata=metadata
        )

    async def get_relevant_context(
        self,
        user_id: str,
        query: str,
        source_types: List[str] = None,
        top_k: int = 5
    ) -> str:
        results = await self.search(user_id, query, source_types, top_k)
        if not results:
            return ""

        parts = []
        for r in results:
            source = r.get("source_type", "unknown").upper()
            content = r.get("content", "")
            similarity = r.get("similarity", 0)
            if similarity > 0.3:
                parts.append(f"[{source}] {content}")

        return "\n\n---\n\n".join(parts)
