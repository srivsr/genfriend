from dataclasses import dataclass
from typing import List, Optional
from .base import BaseAgent, AgentContext, AgentResponse
from app.llm import TaskType
from app.services.embedding_service import EmbeddingService
from app.core.database import async_session


@dataclass
class MemoryResult:
    content: str
    source_type: str
    source_id: str
    date: str
    relevance: float
    metadata: dict = None


class MemoryAgent(BaseAgent):
    name = "memory"
    description = "Personal RAG agent for user's data"

    async def process(self, message: str, context: AgentContext) -> AgentResponse:
        return await self.retrieve_and_reflect(context.user_id, message)

    async def retrieve_and_reflect(self, user_id: str, query: str) -> AgentResponse:
        results = await self._retrieve(user_id, query)

        if not results:
            return AgentResponse(
                content="I don't have any memories about that yet. Would you like to tell me more?",
                confidence=0.3
            )

        context_text = self._build_context(results)

        prompt = f"""Based on these memories, respond to: "{query}"

Memories:
{context_text}

Respond naturally, referencing specific memories when relevant. Be warm and personal.
Connect patterns across different memories when applicable.
If the user asked about progress or achievements, highlight their growth."""

        response = await self._generate(prompt, task_type=TaskType.GENERATION)

        source_data = [
            {"source_type": r.source_type, "source_id": r.source_id, "relevance": r.relevance}
            for r in results
        ]

        return AgentResponse(content=response, data={"sources": source_data}, confidence=0.8)

    async def _retrieve(self, user_id: str, query: str, top_k: int = 5) -> List[MemoryResult]:
        async with async_session() as db:
            service = EmbeddingService(db)
            results = await service.search(
                user_id=user_id,
                query=query,
                top_k=top_k
            )

        memory_results = []
        for r in results:
            if r.get("similarity", 0) > 0.25:
                memory_results.append(MemoryResult(
                    content=r.get("content", ""),
                    source_type=r.get("source_type", "unknown"),
                    source_id=r.get("source_id", ""),
                    date=r.get("metadata", {}).get("created_at", "recent"),
                    relevance=r.get("similarity", 0.5),
                    metadata=r.get("metadata")
                ))

        return memory_results

    async def store_memory(
        self,
        user_id: str,
        content: str,
        source_type: str,
        source_id: str,
        metadata: dict = None
    ) -> str:
        async with async_session() as db:
            service = EmbeddingService(db)
            embedding_id = await service.embed_and_store(
                user_id=user_id,
                content=content,
                source_type=source_type,
                source_id=source_id,
                metadata=metadata
            )
        return embedding_id

    async def search_by_type(
        self,
        user_id: str,
        query: str,
        source_types: List[str],
        top_k: int = 5
    ) -> List[MemoryResult]:
        async with async_session() as db:
            service = EmbeddingService(db)
            results = await service.search(
                user_id=user_id,
                query=query,
                source_types=source_types,
                top_k=top_k
            )

        return [
            MemoryResult(
                content=r.get("content", ""),
                source_type=r.get("source_type", "unknown"),
                source_id=r.get("source_id", ""),
                date=r.get("metadata", {}).get("created_at", "recent"),
                relevance=r.get("similarity", 0.5),
                metadata=r.get("metadata")
            )
            for r in results if r.get("similarity", 0) > 0.25
        ]

    async def get_context_for_planning(self, user_id: str, focus: str) -> str:
        async with async_session() as db:
            service = EmbeddingService(db)
            return await service.get_relevant_context(
                user_id=user_id,
                query=focus,
                source_types=["goal", "task", "journal"],
                top_k=10
            )

    async def get_context_for_coaching(self, user_id: str, topic: str) -> str:
        async with async_session() as db:
            service = EmbeddingService(db)
            return await service.get_relevant_context(
                user_id=user_id,
                query=topic,
                source_types=["journal", "conversation"],
                top_k=8
            )

    def _build_context(self, results: List[MemoryResult]) -> str:
        parts = []
        for r in sorted(results, key=lambda x: x.relevance, reverse=True):
            source_label = r.source_type.upper()
            date_label = r.date if r.date else "recent"
            relevance_pct = int(r.relevance * 100)
            parts.append(f"[{source_label}] ({date_label}, {relevance_pct}% match)\n{r.content}")
        return "\n\n---\n\n".join(parts)


memory_agent = MemoryAgent()
