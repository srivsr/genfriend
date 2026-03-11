"""Tests for SafetyAgent — crisis detection is safety-critical."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.safety import SafetyAgent, SafetyCheck, CRISIS_KEYWORDS, CRISIS_RESPONSE
from app.agents.base import AgentContext


@pytest.fixture
def safety_agent():
    agent = SafetyAgent()
    agent.llm = AsyncMock()
    return agent


class TestKeywordDetection:
    """Crisis keywords MUST always trigger intervention."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("keyword", CRISIS_KEYWORDS)
    async def test_each_crisis_keyword_triggers(self, safety_agent, keyword):
        check = await safety_agent.check(f"I feel like I want to {keyword}")
        assert check.requires_intervention is True
        assert check.severity == "high"
        assert check.response == CRISIS_RESPONSE

    @pytest.mark.asyncio
    async def test_case_insensitive_detection(self, safety_agent):
        check = await safety_agent.check("I want to KILL MYSELF")
        assert check.requires_intervention is True

    @pytest.mark.asyncio
    async def test_keyword_in_longer_message(self, safety_agent):
        check = await safety_agent.check("I've been thinking about things and I just want to end it all because nothing matters anymore")
        assert check.requires_intervention is True
        assert check.severity == "high"

    @pytest.mark.asyncio
    async def test_crisis_response_has_helpline(self, safety_agent):
        check = await safety_agent.check("I want to kill myself")
        assert "988" in check.response  # US helpline
        assert "iCall" in check.response  # India helpline
        assert "findahelpline.com" in check.response


class TestSafeMessages:
    @pytest.mark.asyncio
    async def test_normal_message_passes(self, safety_agent):
        safety_agent.llm.generate = AsyncMock(
            return_value=MagicMock(content='{"concern_level": 0.1, "concern_type": "none"}')
        )
        check = await safety_agent.check("Help me plan my day")
        assert check.requires_intervention is False

    @pytest.mark.asyncio
    async def test_career_question_passes(self, safety_agent):
        safety_agent.llm.generate = AsyncMock(
            return_value=MagicMock(content='{"concern_level": 0.0, "concern_type": "none"}')
        )
        check = await safety_agent.check("How do I improve my coding skills?")
        assert check.requires_intervention is False


class TestLLMBasedDetection:
    @pytest.mark.asyncio
    async def test_high_concern_triggers_medium_intervention(self, safety_agent):
        safety_agent.llm.generate = AsyncMock(
            return_value=MagicMock(content='{"concern_level": 0.8, "concern_type": "harmful-advice"}')
        )
        check = await safety_agent.check("Tell me how to make dangerous things")
        assert check.requires_intervention is True
        assert check.severity == "medium"

    @pytest.mark.asyncio
    async def test_llm_failure_defaults_to_safe(self, safety_agent):
        safety_agent.llm.generate = AsyncMock(side_effect=Exception("LLM down"))
        check = await safety_agent.check("some message")
        # Should NOT crash — defaults to safe
        assert check.requires_intervention is False


class TestProcessMethod:
    @pytest.mark.asyncio
    async def test_process_returns_crisis_response(self, safety_agent):
        ctx = AgentContext(user_id="test")
        response = await safety_agent.process("I want to kill myself", ctx)
        assert response.content == CRISIS_RESPONSE
        assert response.metadata["severity"] == "high"

    @pytest.mark.asyncio
    async def test_process_returns_safe(self, safety_agent):
        safety_agent.llm.generate = AsyncMock(
            return_value=MagicMock(content='{"concern_level": 0.0, "concern_type": "none"}')
        )
        ctx = AgentContext(user_id="test")
        response = await safety_agent.process("Good morning!", ctx)
        assert response.metadata.get("safe") is True
