import logging
import time
from dataclasses import dataclass
from .retriever import hybrid_retriever, RetrievalResult
from .context import context_builder
from app.llm import llm_router, TaskType

logger = logging.getLogger(__name__)

@dataclass
class RAGResponse:
    answer: str
    sources: list[RetrievalResult]
    confidence: float

class RAGPipeline:
    def __init__(self):
        self.retriever = hybrid_retriever
        self.context_builder = context_builder
        self.llm = llm_router

    async def query(self, user_id: str, query: str, sources: list[str] = None) -> RAGResponse:
        retrieval_start = time.time()
        results = await self.retriever.retrieve(user_id=user_id, query=query, sources=sources or ["entries", "tasks", "goals"], top_k=10)
        retrieval_ms = int((time.time() - retrieval_start) * 1000)
        logger.info(f"RAG retrieval: user={user_id} results={len(results)} latency={retrieval_ms}ms")

        if not results:
            return RAGResponse(answer="I don't have enough information to answer that. Tell me more about it!", sources=[], confidence=0.2)

        context = self.context_builder.build(results, include_metadata=True)

        prompt = f"""Answer the following question based on the provided context.
Be personal and reference specific memories when relevant.

Context:
{context}

Question: {query}

Answer naturally, as a supportive companion who knows this person well."""

        response = await self.llm.generate(prompt=prompt, task_type=TaskType.GENERATION, user_id=user_id)

        return RAGResponse(answer=response.content, sources=results, confidence=self._calculate_confidence(results))

    def _calculate_confidence(self, results: list[RetrievalResult]) -> float:
        if not results:
            return 0.0
        avg_score = sum(r.score for r in results) / len(results)
        return min(avg_score * 1.2, 1.0)

rag_pipeline = RAGPipeline()
