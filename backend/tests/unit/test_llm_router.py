"""Tests for LLM Router — provider selection, fallback, cost tracking."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.llm.providers.base import LLMResponse
from app.llm.router import LLMRouter, TaskType


@pytest.fixture
def mock_providers():
    groq = MagicMock()
    groq.generate = AsyncMock(return_value=LLMResponse(content="groq response", input_tokens=10, output_tokens=20, model="llama-3.1-70b"))
    openai = MagicMock()
    openai.generate = AsyncMock(return_value=LLMResponse(content="openai response", input_tokens=15, output_tokens=25, model="gpt-4o"))
    claude = MagicMock()
    claude.generate = AsyncMock(return_value=LLMResponse(content="claude response", input_tokens=12, output_tokens=22, model="claude-sonnet-4-20250514"))
    return {"groq": groq, "openai": openai, "claude": claude}


@pytest.fixture
def router(mock_providers):
    r = LLMRouter.__new__(LLMRouter)
    r.providers = mock_providers
    r.default = "groq"
    r.cost_tracker = MagicMock()
    r.cost_tracker.track = AsyncMock()
    return r


class TestProviderSelection:
    def test_default_classification_uses_groq(self, router):
        provider, model = router._select_model(TaskType.CLASSIFICATION)
        assert provider is router.providers["groq"]

    def test_default_generation_uses_groq(self, router):
        provider, model = router._select_model(TaskType.GENERATION)
        assert provider is router.providers["groq"]

    def test_complex_reasoning_uses_openai(self, router):
        provider, model = router._select_model(TaskType.COMPLEX_REASONING)
        assert provider is router.providers["openai"]
        assert model == "gpt-4o"

    def test_preference_overrides_default(self, router):
        provider, model = router._select_model(TaskType.GENERATION, preference="claude")
        assert provider is router.providers["claude"]

    def test_invalid_preference_ignored(self, router):
        provider, model = router._select_model(TaskType.GENERATION, preference="nonexistent")
        assert provider is router.providers["groq"]  # Falls back to default


class TestGenerate:
    @pytest.mark.asyncio
    async def test_successful_generation(self, router):
        response = await router.generate(prompt="Hello", task_type=TaskType.GENERATION)
        assert response.content == "groq response"
        router.providers["groq"].generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_cost_tracked_with_user_id(self, router):
        await router.generate(prompt="Hello", task_type=TaskType.GENERATION, user_id="user-123")
        router.cost_tracker.track.assert_called_once()
        call_kwargs = router.cost_tracker.track.call_args.kwargs
        assert call_kwargs["user_id"] == "user-123"
        assert call_kwargs["model"] == "llama-3.1-70b"
        assert call_kwargs["request_type"] == "generation"

    @pytest.mark.asyncio
    async def test_no_cost_tracking_without_user_id(self, router):
        await router.generate(prompt="Hello", task_type=TaskType.GENERATION)
        router.cost_tracker.track.assert_not_called()


class TestFallback:
    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self, router):
        router.providers["groq"].generate = AsyncMock(side_effect=Exception("Groq down"))
        response = await router.generate(prompt="Hello", task_type=TaskType.GENERATION)
        assert response.content == "openai response"
        router.providers["openai"].generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_uses_openai(self, router):
        router.providers["groq"].generate = AsyncMock(side_effect=Exception("timeout"))
        response = await router.generate(prompt="test", task_type=TaskType.CLASSIFICATION)
        # Fallback should go to OpenAI
        assert response.model == "gpt-4o"
