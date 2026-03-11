import logging
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=60.0)
        self.model = settings.embedding_model
        self.dimension = settings.embedding_dimension

    async def embed(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(model=self.model, input=text)
        logger.info(f"Embedding: model={self.model} chars={len(text)} tokens={response.usage.total_tokens}")
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(model=self.model, input=texts)
        logger.info(f"Embedding batch: model={self.model} count={len(texts)} tokens={response.usage.total_tokens}")
        return [item.embedding for item in response.data]

embedding_service = EmbeddingService()
