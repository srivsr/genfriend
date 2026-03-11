"""Tests for InsightAgent — insight classification and data gathering."""
import pytest
from app.agents.insight import InsightAgent, InsightType


@pytest.fixture
def insight_agent():
    from unittest.mock import AsyncMock
    agent = InsightAgent()
    agent.llm = AsyncMock()
    return agent


class TestInsightClassification:
    def test_productivity(self, insight_agent):
        assert insight_agent._classify_insight_request("How productive was I?") == InsightType.PRODUCTIVITY

    def test_emotional_trend(self, insight_agent):
        assert insight_agent._classify_insight_request("How have I been feeling?") == InsightType.EMOTIONAL_TREND

    def test_goal_progress(self, insight_agent):
        assert insight_agent._classify_insight_request("Show goal progress") == InsightType.GOAL_PROGRESS

    def test_blockers(self, insight_agent):
        assert insight_agent._classify_insight_request("What's blocking me?") == InsightType.BLOCKERS

    def test_weekly_summary(self, insight_agent):
        assert insight_agent._classify_insight_request("Give me a week summary") == InsightType.WEEKLY_SUMMARY

    def test_patterns(self, insight_agent):
        assert insight_agent._classify_insight_request("Show me my habit patterns") == InsightType.PATTERNS

    def test_default_productivity(self, insight_agent):
        assert insight_agent._classify_insight_request("Tell me something") == InsightType.PRODUCTIVITY

    def test_task_keyword(self, insight_agent):
        assert insight_agent._classify_insight_request("How many tasks did I do?") == InsightType.PRODUCTIVITY

    def test_mood_keyword(self, insight_agent):
        assert insight_agent._classify_insight_request("my mood this month") == InsightType.EMOTIONAL_TREND

    def test_obstacle_keyword(self, insight_agent):
        assert insight_agent._classify_insight_request("What obstacles am I facing?") == InsightType.BLOCKERS
