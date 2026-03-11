"""Tests for PlannerAgent — plan parsing, daily/weekly routing."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.planner import PlannerAgent, PlanTask, DailyPlan
from app.agents.base import AgentContext


@pytest.fixture
def planner():
    agent = PlannerAgent()
    agent.llm = AsyncMock()
    return agent


class TestParsePlan:
    def test_parses_valid_plan(self, planner):
        response = """morning|high|Deep work: Complete project proposal
afternoon|medium|Learn: 30-min skill tutorial
evening|low|Reflect: Journal about today's wins"""
        tasks = planner._parse_plan(response)
        assert len(tasks) == 3
        assert tasks[0].time_block == "morning"
        assert tasks[0].priority == "high"
        assert tasks[0].title == "Deep work: Complete project proposal"

    def test_handles_markdown_in_response(self, planner):
        response = "**morning**|**high**|**Deep work on code**"
        tasks = planner._parse_plan(response)
        assert len(tasks) == 1
        assert tasks[0].time_block == "morning"
        assert "**" not in tasks[0].title

    def test_skips_non_plan_lines(self, planner):
        response = """Here's your plan for today:
morning|high|Review pull requests
This is going to be a great day!
afternoon|medium|Team standup"""
        tasks = planner._parse_plan(response)
        assert len(tasks) == 2

    def test_empty_response(self, planner):
        tasks = planner._parse_plan("")
        assert tasks == []

    def test_malformed_lines_skipped(self, planner):
        response = "morning|high"  # Only 2 parts, needs 3
        tasks = planner._parse_plan(response)
        assert tasks == []


class TestProcess:
    @pytest.mark.asyncio
    async def test_daily_plan_default(self, planner):
        ctx = AgentContext(user_id="test")
        planner.llm.generate = AsyncMock(
            return_value=MagicMock(content="morning|high|Code review\nSummary line")
        )
        with patch("app.agents.planner.identity_builder") as mock_id, \
             patch("app.agents.planner.get_user_goals") as mock_goals:
            mock_id.get_identity = AsyncMock(return_value=None)
            mock_goals.return_value = []
            response = await planner.process("plan my day", ctx)
        assert response.content  # Has summary
        assert response.data["plan"] is not None

    @pytest.mark.asyncio
    async def test_weekly_plan_on_week_keyword(self, planner):
        ctx = AgentContext(user_id="test")
        planner.llm.generate = AsyncMock(
            return_value=MagicMock(content="Weekly plan summary")
        )
        response = await planner.process("plan this week", ctx)
        assert response.data["plan"].date == "This Week"


class TestDailyPlanWithContext:
    @pytest.mark.asyncio
    async def test_identity_context_included_in_prompt(self, planner):
        with patch("app.agents.planner.identity_builder") as mock_id, \
             patch("app.agents.planner.get_user_goals") as mock_goals:
            mock_id.get_identity = AsyncMock(return_value={
                "ideal_self": "Senior Engineer",
                "why": "technical mastery",
                "attributes": ["focused", "disciplined"]
            })
            mock_goals.return_value = [
                {"title": "Learn Rust", "progress_percent": 30}
            ]
            planner.llm.generate = AsyncMock(
                return_value=MagicMock(content="morning|high|Study Rust\nKeep going!")
            )
            plan = await planner.create_daily_plan("test-user")

        # Verify LLM was called with identity context
        call_args = planner.llm.generate.call_args
        prompt = call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")
        assert "Senior Engineer" in prompt
        assert "Learn Rust" in prompt
