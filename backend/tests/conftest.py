"""Shared test fixtures for gen-friend-v3."""
import os
import sys
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

# Ensure app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set test environment BEFORE any app imports
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_genfriend.db"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# --- LLM Mock Fixtures ---

@dataclass
class FakeLLMResponse:
    content: str = "Test response"
    input_tokens: int = 10
    output_tokens: int = 20
    model: str = "test-model"


@pytest.fixture
def mock_llm_router():
    """Mock LLM router that returns deterministic responses."""
    router = AsyncMock()
    router.generate = AsyncMock(return_value=FakeLLMResponse())
    return router


@pytest.fixture
def patch_llm_router(mock_llm_router):
    """Patch the global llm_router singleton."""
    with patch("app.llm.router.llm_router", mock_llm_router), \
         patch("app.llm.llm_router", mock_llm_router):
        yield mock_llm_router


# --- Agent Context Fixtures ---

@pytest.fixture
def agent_context():
    from app.agents.base import AgentContext
    return AgentContext(
        user_id="test-user-001",
        conversation_history=[
            {"role": "user", "content": "Hello"},
            {"role": "mentor", "content": "Hi there! How can I help?"},
        ],
    )


@pytest.fixture
def empty_context():
    from app.agents.base import AgentContext
    return AgentContext(user_id="test-user-001")


# --- Database Fixtures ---

@pytest.fixture
async def async_db():
    """In-memory SQLite async session for tests."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Import all models so tables are created
    from app.models.user import User  # noqa: F401
    from app.models.conversation import Conversation, Message  # noqa: F401
    from sqlalchemy.orm import DeclarativeBase

    # Get the Base class from models
    try:
        from app.core.database import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        pass

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


# --- Auth Fixtures ---

DEV_USER_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def auth_headers():
    """Headers for authenticated requests (dev mode bypasses actual auth)."""
    return {"Authorization": "Bearer test-token"}


# --- FastAPI Test Client ---

@pytest.fixture
def test_app():
    """FastAPI test app with dependency overrides."""
    from app.main import app
    return app


@pytest.fixture
def client(test_app):
    """Sync HTTP test client for integration tests."""
    from fastapi.testclient import TestClient
    with TestClient(test_app) as tc:
        yield tc
