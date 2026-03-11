from dataclasses import dataclass, field
from collections import defaultdict
from typing import List, Optional, Dict, Any
import json
import re
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .embeddings import embedding_service
from app.core.database import async_session
from app.models.embedding import Embedding, PGVECTOR_AVAILABLE
from app.models.journal import JournalEntry
from app.models.goal import Goal
from app.models.task import Task


@dataclass
class RetrievalResult:
    id: str
    content: str
    source_type: str
    date: str
    score: float
    metadata: dict = field(default_factory=dict)
    citation: str = ""


@dataclass
class CitedResult:
    content: str
    source: str
    citation_number: int
    formatted_citation: str


class HybridRetriever:
    def __init__(self):
        self.embeddings = embedding_service

    async def retrieve(
        self,
        user_id: str,
        query: str,
        sources: Optional[List[str]] = None,
        top_k: int = 10,
        db: Optional[AsyncSession] = None
    ) -> List[RetrievalResult]:
        query_embedding = await self.embeddings.embed(query)
        should_close = False
        if db is None:
            db = async_session()
            should_close = True

        try:
            vector_results = await self._vector_search(db, user_id, query_embedding, sources, top_k * 2)
            bm25_results = await self._bm25_search(db, user_id, query, sources, top_k * 2)
            fused = self._reciprocal_rank_fusion(vector_results, bm25_results, k=60)
            for result in fused:
                result.citation = self._generate_citation(result)
            return fused[:top_k]
        finally:
            if should_close:
                await db.close()

    async def _vector_search(
        self,
        db: AsyncSession,
        user_id: str,
        embedding: List[float],
        sources: Optional[List[str]],
        top_k: int
    ) -> List[RetrievalResult]:
        results = []
        if PGVECTOR_AVAILABLE:
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
            source_filter = ""
            params = {"user_id": user_id, "embedding": embedding_str, "limit": top_k}
            if sources:
                placeholders = ", ".join([f":src_{i}" for i in range(len(sources))])
                source_filter = f"AND source_type IN ({placeholders})"
                for i, s in enumerate(sources):
                    params[f"src_{i}"] = s

            query = text(f"""
                SELECT id, user_id, source_type, source_id, content_preview, metadata,
                       created_at, 1 - (embedding <=> :embedding::vector) as similarity
                FROM embeddings
                WHERE user_id = :user_id {source_filter}
                ORDER BY embedding <=> :embedding::vector
                LIMIT :limit
            """)
            result = await db.execute(query, params)
            rows = result.fetchall()
            for row in rows:
                results.append(RetrievalResult(
                    id=row.id,
                    content=row.content_preview or "",
                    source_type=row.source_type,
                    date=row.created_at.isoformat() if row.created_at else "",
                    score=float(row.similarity) if row.similarity else 0.0,
                    metadata=row.metadata or {}
                ))
        else:
            query = select(Embedding).where(Embedding.user_id == user_id)
            if sources:
                query = query.where(Embedding.source_type.in_(sources))
            query = query.limit(top_k * 3)
            result = await db.execute(query)
            embeddings = result.scalars().all()

            for emb in embeddings:
                if emb.embedding:
                    try:
                        stored_emb = json.loads(emb.embedding) if isinstance(emb.embedding, str) else emb.embedding
                        similarity = self._cosine_similarity(embedding, stored_emb)
                        results.append(RetrievalResult(
                            id=emb.id,
                            content=emb.content_preview or "",
                            source_type=emb.source_type,
                            date=emb.created_at.isoformat() if emb.created_at else "",
                            score=similarity,
                            metadata=emb.metadata_ or {}
                        ))
                    except:
                        continue

            results.sort(key=lambda x: x.score, reverse=True)
            results = results[:top_k]

        return results

    async def _bm25_search(
        self,
        db: AsyncSession,
        user_id: str,
        query: str,
        sources: Optional[List[str]],
        top_k: int
    ) -> List[RetrievalResult]:
        results = []
        keywords = self._extract_keywords(query)
        if not keywords:
            return results
        keyword_pattern = "|".join(keywords)

        if not sources or "journal" in sources:
            journal_query = select(JournalEntry).where(
                JournalEntry.user_id == user_id
            ).order_by(JournalEntry.created_at.desc()).limit(top_k * 2)
            result = await db.execute(journal_query)
            entries = result.scalars().all()
            for entry in entries:
                content = entry.content or ""
                score = self._simple_bm25_score(content, keywords)
                if score > 0:
                    results.append(RetrievalResult(
                        id=f"journal_{entry.id}",
                        content=content[:500],
                        source_type="journal",
                        date=entry.created_at.isoformat() if entry.created_at else "",
                        score=score,
                        metadata={"entry_type": entry.entry_type, "tags": entry.tags}
                    ))

        if not sources or "goal" in sources:
            goal_query = select(Goal).where(Goal.user_id == user_id).limit(top_k)
            result = await db.execute(goal_query)
            goals = result.scalars().all()
            for goal in goals:
                content = f"{goal.title} {goal.description or ''} {goal.why or ''}"
                score = self._simple_bm25_score(content, keywords)
                if score > 0:
                    results.append(RetrievalResult(
                        id=f"goal_{goal.id}",
                        content=content[:500],
                        source_type="goal",
                        date=goal.created_at.isoformat() if goal.created_at else "",
                        score=score,
                        metadata={
                            "status": goal.status,
                            "progress": goal.progress_percent,
                            "obstacle": goal.woop_primary_obstacle
                        }
                    ))

        if not sources or "task" in sources:
            task_query = select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc()).limit(top_k * 2)
            result = await db.execute(task_query)
            tasks = result.scalars().all()
            for task in tasks:
                content = f"{task.title} {task.outcome_notes or ''}"
                score = self._simple_bm25_score(content, keywords)
                if score > 0:
                    results.append(RetrievalResult(
                        id=f"task_{task.id}",
                        content=content[:500],
                        source_type="task",
                        date=task.created_at.isoformat() if task.created_at else "",
                        score=score,
                        metadata={"status": task.status, "goal_id": task.goal_id}
                    ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _reciprocal_rank_fusion(self, *result_lists: List[RetrievalResult], k: int = 60) -> List[RetrievalResult]:
        scores = defaultdict(float)
        docs = {}
        for results in result_lists:
            for rank, result in enumerate(results):
                scores[result.id] += 1 / (k + rank + 1)
                if result.id not in docs or result.score > docs[result.id].score:
                    docs[result.id] = result
        for doc_id in docs:
            docs[doc_id].score = scores[doc_id]
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [docs[id] for id in sorted_ids]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if len(vec1) != len(vec2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def _extract_keywords(self, query: str) -> List[str]:
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                      "have", "has", "had", "do", "does", "did", "will", "would", "could",
                      "should", "may", "might", "must", "to", "of", "in", "for", "on", "with",
                      "at", "by", "from", "as", "into", "through", "during", "before", "after",
                      "above", "below", "between", "under", "again", "further", "then", "once",
                      "here", "there", "when", "where", "why", "how", "all", "each", "few",
                      "more", "most", "other", "some", "such", "no", "nor", "not", "only",
                      "own", "same", "so", "than", "too", "very", "can", "just", "i", "me",
                      "my", "myself", "we", "our", "you", "your", "he", "him", "his", "she",
                      "her", "it", "its", "they", "them", "their", "what", "which", "who"}
        words = re.findall(r'\b\w+\b', query.lower())
        return [w for w in words if w not in stop_words and len(w) > 2]

    def _simple_bm25_score(self, content: str, keywords: List[str]) -> float:
        if not content or not keywords:
            return 0.0
        content_lower = content.lower()
        score = 0.0
        for keyword in keywords:
            count = content_lower.count(keyword)
            if count > 0:
                score += 1 + (count - 1) * 0.5
        return score

    def _generate_citation(self, result: RetrievalResult) -> str:
        source_type = result.source_type
        date = result.date[:10] if result.date else "unknown date"
        if source_type == "journal":
            entry_type = result.metadata.get("entry_type", "entry")
            return f"[Your {entry_type}, {date}]"
        elif source_type == "goal":
            status = result.metadata.get("status", "")
            return f"[Goal: {result.content[:50]}..., {status}]"
        elif source_type == "task":
            status = result.metadata.get("status", "")
            return f"[Task, {date}, {status}]"
        elif source_type == "reflection":
            return f"[Your reflection, {date}]"
        return f"[{source_type}, {date}]"


def format_with_citations(results: List[RetrievalResult], response_text: str) -> str:
    citations = []
    for i, result in enumerate(results, 1):
        citations.append(f"[{i}] {result.citation}")
    if citations:
        return f"{response_text}\n\n**Sources:**\n" + "\n".join(citations)
    return response_text


hybrid_retriever = HybridRetriever()
