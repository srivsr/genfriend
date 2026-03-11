"""Base model utilities for database-agnostic UUID support."""
from sqlalchemy import Column, String
import uuid

def uuid_column(primary_key=False, nullable=False, index=False):
    """Create a UUID column that works with both PostgreSQL and SQLite."""
    return Column(
        String(36),
        primary_key=primary_key,
        nullable=nullable,
        index=index,
        default=lambda: str(uuid.uuid4()) if primary_key else None
    )

def new_uuid():
    return str(uuid.uuid4())
