from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.embedding import Embedding
from app.config import settings

class EmbeddingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def store(
        self,
        user_id: str,
        content: str,
        source_type: str,
        source_id: str,
        embedding: List[float],
        metadata: dict = None
    ) -> Embedding:
        import uuid
        embedding_str = str(embedding) if not settings.pgvector_available else embedding

        instance = Embedding(
            id=str(uuid.uuid4()),
            user_id=user_id,
            source_type=source_type,
            source_id=source_id,
            content_preview=content[:500] if content else "",
            embedding=embedding_str,
            metadata_=metadata or {}
        )
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete_by_source(self, source_id: str, user_id: str = None) -> bool:
        """
        Delete embedding by source_id.

        SECURITY: If user_id is provided, only delete if it belongs to that user.
        """
        from sqlalchemy import delete

        if user_id:
            # SECURITY FIX: Only delete if embedding belongs to the user
            result = await self.db.execute(
                delete(Embedding).where(
                    Embedding.source_id == source_id,
                    Embedding.user_id == user_id
                )
            )
        else:
            # For internal/admin use only - should be avoided in user-facing code
            result = await self.db.execute(
                delete(Embedding).where(Embedding.source_id == source_id)
            )
        await self.db.commit()
        return result.rowcount > 0

    async def vector_search(
        self,
        user_id: str,
        query_embedding: List[float],
        source_types: List[str] = None,
        top_k: int = 10
    ) -> List[dict]:
        if not settings.pgvector_available:
            return await self._fallback_search(user_id, source_types, top_k)

        embedding_str = str(query_embedding)
        base_sql = """
            SELECT
                id, source_type, source_id, content_preview, metadata,
                1 - (embedding <=> :query_embedding::vector) as similarity
            FROM embeddings
            WHERE user_id = :user_id
        """

        params = {
            "user_id": user_id,
            "query_embedding": embedding_str,
            "top_k": top_k
        }

        if source_types:
            base_sql += " AND source_type = ANY(:source_types)"
            params["source_types"] = source_types

        base_sql += """
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :top_k
        """

        result = await self.db.execute(text(base_sql), params)
        rows = result.fetchall()

        return [
            {
                "id": str(row.id),
                "source_type": row.source_type,
                "source_id": row.source_id,
                "content": row.content_preview,
                "metadata": row.metadata,
                "similarity": float(row.similarity)
            }
            for row in rows
        ]

    async def _fallback_search(
        self,
        user_id: str,
        source_types: List[str] = None,
        top_k: int = 10
    ) -> List[dict]:
        query = select(Embedding).where(Embedding.user_id == user_id)
        if source_types:
            query = query.where(Embedding.source_type.in_(source_types))
        query = query.order_by(Embedding.created_at.desc()).limit(top_k)

        result = await self.db.execute(query)
        embeddings = list(result.scalars().all())

        return [
            {
                "id": str(e.id),
                "source_type": e.source_type,
                "source_id": e.source_id,
                "content": e.content_preview,
                "metadata": e.metadata_,
                "similarity": 0.5
            }
            for e in embeddings
        ]

    async def get_by_user(self, user_id: str, limit: int = 100) -> List[Embedding]:
        result = await self.db.execute(
            select(Embedding)
            .where(Embedding.user_id == user_id)
            .order_by(Embedding.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: str) -> int:
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(Embedding.id)).where(Embedding.user_id == user_id)
        )
        return result.scalar() or 0
