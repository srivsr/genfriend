"""Knowledge loader for RAG system - loads domain-specific knowledge files."""
import os
from pathlib import Path
from typing import Dict, List, Optional
from app.rag.embeddings import EmbeddingsService
from app.rag.vectorstore import VectorStore

KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent.parent / "knowledge"

DOMAIN_CATEGORIES = {
    "ceo": ["skills", "habits", "decision_frameworks"],
    "entrepreneur": ["skills", "habits", "decision_frameworks"],
    "musician": ["skills", "habits", "decision_frameworks"],
    "doctor": ["skills", "habits", "decision_frameworks"],
    "general": ["productivity", "goal_setting", "mindset", "communication"],
}


class KnowledgeLoader:
    def __init__(
        self,
        embeddings_service: EmbeddingsService,
        vector_store: VectorStore
    ):
        self.embeddings = embeddings_service
        self.vector_store = vector_store

    def load_domain_knowledge(self, domain: str) -> List[Dict]:
        """Load all knowledge files for a specific domain."""
        if domain not in DOMAIN_CATEGORIES:
            return []

        documents = []
        domain_path = KNOWLEDGE_BASE_PATH / domain

        for file_name in DOMAIN_CATEGORIES[domain]:
            file_path = domain_path / f"{file_name}.md"
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                chunks = self._chunk_content(content, domain, file_name)
                documents.extend(chunks)

        return documents

    def load_all_knowledge(self) -> List[Dict]:
        """Load knowledge from all domains."""
        all_documents = []
        for domain in DOMAIN_CATEGORIES:
            documents = self.load_domain_knowledge(domain)
            all_documents.extend(documents)
        return all_documents

    def _chunk_content(
        self,
        content: str,
        domain: str,
        category: str,
        chunk_size: int = 500
    ) -> List[Dict]:
        """Split content into chunks by sections."""
        chunks = []
        sections = content.split("\n## ")

        for i, section in enumerate(sections):
            if not section.strip():
                continue

            if i == 0 and section.startswith("# "):
                lines = section.split("\n", 1)
                title = lines[0].replace("# ", "")
                section_content = lines[1] if len(lines) > 1 else ""
            else:
                lines = section.split("\n", 1)
                title = lines[0]
                section_content = lines[1] if len(lines) > 1 else ""

            if not section_content.strip():
                continue

            chunks.append({
                "content": section_content.strip(),
                "metadata": {
                    "domain": domain,
                    "category": category,
                    "section": title,
                    "source": f"{domain}/{category}.md"
                }
            })

        return chunks

    async def index_knowledge(self, domain: Optional[str] = None) -> int:
        """Index knowledge into vector store."""
        if domain:
            documents = self.load_domain_knowledge(domain)
        else:
            documents = self.load_all_knowledge()

        indexed = 0
        for doc in documents:
            embedding = await self.embeddings.embed(doc["content"])
            await self.vector_store.add(
                content=doc["content"],
                embedding=embedding,
                metadata=doc["metadata"]
            )
            indexed += 1

        return indexed

    def get_relevant_domains(self, ideal_self: str) -> List[str]:
        """Map user's ideal self to relevant knowledge domains."""
        ideal_lower = ideal_self.lower()

        domain_keywords = {
            "ceo": ["ceo", "executive", "leader", "c-suite", "chief"],
            "entrepreneur": ["entrepreneur", "founder", "startup", "business owner"],
            "musician": ["musician", "singer", "artist", "producer", "composer"],
            "doctor": ["doctor", "physician", "surgeon", "medical", "healthcare"],
        }

        matched = []
        for domain, keywords in domain_keywords.items():
            if any(kw in ideal_lower for kw in keywords):
                matched.append(domain)

        matched.append("general")
        return matched
