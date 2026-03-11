"""Tests for MentorEngine — persona building, context gathering, response generation."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.mentor.engine import MentorEngine, MentorContext, MentorResponse, MENTOR_PERSONA
from app.llm.providers.base import LLMResponse


@pytest.fixture
def engine():
    e = MentorEngine.__new__(MentorEngine)
    e.identity_builder = MagicMock()
    e.goal_coach = MagicMock()
    e.pattern_detector = MagicMock()
    e.journal_keeper = MagicMock()
    e.llm = AsyncMock()
    return e


class TestBuildPersona:
    def test_persona_with_identity(self, engine):
        ctx = MentorContext(
            user_id="test",
            identity={"ideal_self": "CTO", "why": "lead innovation", "attributes": ["strategic", "technical"]},
        )
        persona = engine._build_persona(ctx)
        assert "CTO" in persona
        assert "lead innovation" in persona
        assert "strategic" in persona

    def test_persona_without_identity(self, engine):
        ctx = MentorContext(user_id="test", identity=None)
        persona = engine._build_persona(ctx)
        assert "your best self" in persona

    def test_persona_with_empty_attributes(self, engine):
        ctx = MentorContext(user_id="test", identity={"ideal_self": "Leader", "why": "impact", "attributes": []})
        persona = engine._build_persona(ctx)
        assert "focused" in persona  # default attributes


class TestFormatters:
    def test_format_goals_empty(self, engine):
        assert "No active goals" in engine._format_goals([])

    def test_format_goals_with_data(self, engine):
        goals = [{"title": "Learn Python", "progress_percent": 50, "description": "Master Python"}]
        result = engine._format_goals(goals)
        assert "Learn Python" in result
        assert "50%" in result

    def test_format_goals_limits_to_3(self, engine):
        goals = [{"title": f"Goal {i}", "progress_percent": i * 10} for i in range(5)]
        result = engine._format_goals(goals)
        assert "Goal 0" in result
        assert "Goal 2" in result
        assert "Goal 3" not in result  # Only first 3

    def test_format_patterns_empty(self, engine):
        assert "No patterns" in engine._format_patterns([])

    def test_format_patterns_with_data(self, engine):
        patterns = [{"description": "You work best in mornings"}]
        result = engine._format_patterns(patterns)
        assert "mornings" in result

    def test_format_wins_empty(self, engine):
        assert "No wins" in engine._format_wins([])

    def test_format_wins_with_data(self, engine):
        wins = [{"content": "Completed the project milestone ahead of schedule"}]
        result = engine._format_wins(wins)
        assert "milestone" in result


class TestProcess:
    @pytest.mark.asyncio
    async def test_no_identity_prompts_setup(self, engine):
        engine.identity_builder.get_identity = AsyncMock(return_value=None)
        response = await engine.process("test-user", "hello")
        assert "ideal self" in response.content.lower() or "who you want to become" in response.content.lower()

    @pytest.mark.asyncio
    async def test_with_identity_generates_response(self, engine):
        engine.identity_builder.get_identity = AsyncMock(
            return_value={"ideal_self": "CEO", "why": "impact", "attributes": ["decisive"]}
        )
        engine.goal_coach.get_active_goals = AsyncMock(return_value=[])
        engine.pattern_detector.get_recent_patterns = AsyncMock(return_value=[])
        engine.journal_keeper.get_recent_wins = AsyncMock(return_value=[])
        engine.llm.generate = AsyncMock(
            return_value=LLMResponse(content="As the CEO you're becoming...", input_tokens=100, output_tokens=50, model="groq")
        )

        response = await engine.process("test-user", "I need motivation")
        assert response.content == "As the CEO you're becoming..."
        assert response.context_used["identity"] is not None

    @pytest.mark.asyncio
    async def test_context_gathering_calls_all_sources(self, engine):
        engine.identity_builder.get_identity = AsyncMock(return_value={"ideal_self": "Dev"})
        engine.goal_coach.get_active_goals = AsyncMock(return_value=[])
        engine.pattern_detector.get_recent_patterns = AsyncMock(return_value=[])
        engine.journal_keeper.get_recent_wins = AsyncMock(return_value=[])

        ctx = await engine._gather_context("test-user")
        engine.identity_builder.get_identity.assert_called_once_with("test-user")
        engine.goal_coach.get_active_goals.assert_called_once()
        engine.pattern_detector.get_recent_patterns.assert_called_once()
        engine.journal_keeper.get_recent_wins.assert_called_once()
