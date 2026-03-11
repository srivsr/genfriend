"""Tests for EmotionAgent — emotional detection and tone guidance."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.emotion import EmotionAgent, EmotionalState, ToneGuidance
from app.agents.base import AgentContext


@pytest.fixture
def emotion_agent():
    agent = EmotionAgent()
    agent.llm = AsyncMock()
    return agent


@pytest.fixture
def context():
    return AgentContext(user_id="test-user")


class TestEmotionDetection:
    @pytest.mark.asyncio
    async def test_parses_llm_response(self, emotion_agent, context):
        emotion_agent.llm.generate = AsyncMock(
            return_value=MagicMock(content="stressed|4|0.85")
        )
        state = await emotion_agent.detect("I'm overwhelmed with work", context)
        assert state.primary == "stressed"
        assert state.intensity == 4
        assert state.confidence == 0.85

    @pytest.mark.asyncio
    async def test_defaults_on_parse_failure(self, emotion_agent, context):
        emotion_agent.llm.generate = AsyncMock(
            return_value=MagicMock(content="garbled response that cannot be parsed")
        )
        state = await emotion_agent.detect("hello", context)
        assert state.primary == "neutral"
        assert state.intensity == 3
        assert state.confidence == 0.5

    @pytest.mark.asyncio
    async def test_defaults_on_llm_error(self, emotion_agent, context):
        emotion_agent.llm.generate = AsyncMock(side_effect=Exception("timeout"))
        state = await emotion_agent.detect("hello", context)
        assert state.primary == "neutral"

    @pytest.mark.asyncio
    async def test_context_history_included(self, emotion_agent):
        ctx = AgentContext(
            user_id="test",
            conversation_history=[
                {"role": "user", "content": "I feel terrible"},
                {"role": "mentor", "content": "I'm sorry to hear that"}
            ]
        )
        emotion_agent.llm.generate = AsyncMock(
            return_value=MagicMock(content="sad|4|0.9")
        )
        state = await emotion_agent.detect("Nothing is going right", ctx)
        # Verify history was passed to LLM
        call_args = emotion_agent.llm.generate.call_args
        prompt = call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")
        assert "I feel terrible" in prompt


class TestToneGuidance:
    def test_stressed_tone(self, emotion_agent):
        state = EmotionalState(primary="stressed", intensity=4, confidence=0.8)
        guidance = emotion_agent.get_tone_guidance(state)
        assert "calm" in guidance.style.lower() or "supportive" in guidance.style.lower()
        assert "pressure" in guidance.avoid.lower()

    def test_overwhelmed_tone(self, emotion_agent):
        state = EmotionalState(primary="overwhelmed", intensity=5, confidence=0.9)
        guidance = emotion_agent.get_tone_guidance(state)
        assert "supportive" in guidance.style.lower() or "calm" in guidance.style.lower()

    def test_sad_tone(self, emotion_agent):
        state = EmotionalState(primary="sad", intensity=3, confidence=0.7)
        guidance = emotion_agent.get_tone_guidance(state)
        assert "warm" in guidance.style.lower() or "empathetic" in guidance.style.lower()
        assert "toxic positivity" in guidance.avoid.lower()

    def test_frustrated_tone(self, emotion_agent):
        state = EmotionalState(primary="frustrated", intensity=4, confidence=0.8)
        guidance = emotion_agent.get_tone_guidance(state)
        assert "solution" in guidance.style.lower() or "understanding" in guidance.style.lower()

    def test_positive_tone(self, emotion_agent):
        state = EmotionalState(primary="positive", intensity=4, confidence=0.9)
        guidance = emotion_agent.get_tone_guidance(state)
        assert "energetic" in guidance.style.lower() or "encouraging" in guidance.style.lower()

    def test_excited_tone(self, emotion_agent):
        state = EmotionalState(primary="excited", intensity=5, confidence=0.9)
        guidance = emotion_agent.get_tone_guidance(state)
        assert "dampening" in guidance.avoid.lower()

    def test_neutral_tone(self, emotion_agent):
        state = EmotionalState(primary="neutral", intensity=3, confidence=0.5)
        guidance = emotion_agent.get_tone_guidance(state)
        assert "balanced" in guidance.style.lower()


class TestProcess:
    @pytest.mark.asyncio
    async def test_process_returns_state_and_guidance(self, emotion_agent, context):
        emotion_agent.llm.generate = AsyncMock(
            return_value=MagicMock(content="positive|4|0.9")
        )
        response = await emotion_agent.process("I got a promotion!", context)
        assert response.data["state"].primary == "positive"
        assert isinstance(response.data["guidance"], ToneGuidance)
