from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.sql import func
import uuid
from app.core.database import Base
from app.config import settings

# Check both: pgvector installed AND using PostgreSQL database
def _use_pgvector():
    try:
        from pgvector.sqlalchemy import Vector
        return settings.pgvector_available  # Checks if PostgreSQL
    except ImportError:
        return False

USE_PGVECTOR = _use_pgvector()

def get_embedding_column():
    if USE_PGVECTOR:
        from pgvector.sqlalchemy import Vector
        return Column(Vector(settings.embedding_dimension))
    return Column(Text)

class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)
    source_id = Column(String(36), nullable=False)
    content_preview = Column(String(500))
    embedding = get_embedding_column()
    metadata_ = Column("metadata", JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
