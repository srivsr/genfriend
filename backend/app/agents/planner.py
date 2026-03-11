from dataclasses import dataclass
from datetime import datetime
from .base import BaseAgent, AgentContext, AgentResponse
from app.llm import TaskType
from app.mentor.identity import identity_builder


async def get_user_goals(user_id: str):
    """Fetch active goals using a fresh DB session."""
    from app.core.database import async_session
    from app.repositories.goal_repository import GoalRepository
    async with async_session() as db:
        repo = GoalRepository(db)
        goals = await repo.get_active(user_id)
        return [{"title": g.title, "progress_percent": g.progress_percent or 0,
                 "description": g.description, "why": g.why} for g in goals]

@dataclass
class PlanTask:
    title: str
    time_block: str
    priority: str
    goal_link: str | None = None

@dataclass
class DailyPlan:
    date: str
    tasks: list[PlanTask]
    summary: str

class PlannerAgent(BaseAgent):
    name = "planner"
    description = "Creates intelligent, personalized daily/weekly plans"

    async def process(self, message: str, context: AgentContext) -> AgentResponse:
        if "week" in message.lower():
            plan = await self.create_weekly_plan(context.user_id)
        else:
            plan = await self.create_daily_plan(context.user_id)
        return AgentResponse(content=plan.summary, data={"plan": plan})

    async def create_daily_plan(self, user_id: str) -> DailyPlan:
        today = datetime.now().strftime("%A, %B %d")

        # Get user's identity and goals for personalization
        identity = await identity_builder.get_identity(user_id)
        goals = await get_user_goals(user_id)

        # Check distraction rules and anti-goals
        from .strategic_brain import StrategicBrainAgent
        strategic_agent = StrategicBrainAgent()
        violations = await strategic_agent.check_distraction_rules(user_id)
        anti_goals = identity.get("anti_goals", []) if identity else []

        # Build context from user data
        identity_context = ""
        if identity:
            identity_context = f"""
User's Identity:
- Ideal self: {identity.get('ideal_self', 'successful professional')}
- Why: {identity.get('why', 'personal growth')}
- Key attributes: {', '.join(identity.get('attributes', ['focused', 'productive']))}
"""

        goals_context = ""
        if goals:
            goals_list = [f"- {g.get('title', 'Goal')} ({g.get('progress_percent', 0)}% complete)" for g in goals[:3]]
            goals_context = f"""
User's Active Goals:
{chr(10).join(goals_list)}
"""

        constraints = identity.get("constraints", {}) if identity else {}
        constraints_context = ""
        if any(v is not None for v in constraints.values()):
            parts = []
            if constraints.get("weekly_hours_available") is not None:
                parts.append(f"- Available hours per week: {constraints['weekly_hours_available']}")
            if constraints.get("monthly_budget") is not None:
                parts.append(f"- Monthly budget: ${constraints['monthly_budget']}")
            if constraints.get("health_limits"):
                parts.append(f"- Health limits: {constraints['health_limits']}")
            if constraints.get("risk_tolerance"):
                parts.append(f"- Risk tolerance: {constraints['risk_tolerance']}")
            constraints_context = "\nUser's Constraints:\n" + "\n".join(parts)

        anti_goals_context = ""
        if anti_goals:
            anti_goals_context = f"\nAnti-Goals (AVOID these):\n" + "\n".join(f"- {ag}" for ag in anti_goals)

        violations_context = ""
        if violations:
            violations_context = "\nActive Focus Rule Violations:\n" + "\n".join(
                f"- {v.get('rule', 'Rule')}: {v.get('violation', '')}" for v in violations
            )

        prompt = f"""Create a personalized daily plan for today ({today}).
{identity_context}
{goals_context}
{constraints_context}
{anti_goals_context}
{violations_context}
Create a realistic, achievable plan with 3-5 tasks that:
1. Directly support the user's goals and identity
2. Prioritize high-impact tasks during peak energy times (morning: focused work, afternoon: meetings/collaboration, evening: reflection)
3. Include at least one task that moves toward each active goal
4. Be specific and actionable
5. Respect anti-goals — never suggest tasks that conflict with them
6. Address any focus rule violations by prioritizing existing commitments
7. Stay within the user's constraints — respect available hours, budget limits, health limits, and risk tolerance

Format each task as: time_block|priority|title
Example:
morning|high|Deep work: Complete project proposal draft
afternoon|medium|Learn: 30-min skill tutorial
evening|low|Reflect: Journal about today's wins

End with a personalized motivational summary that references their ideal self."""

        response = await self._generate(prompt, task_type=TaskType.GENERATION)
        tasks = self._parse_plan(response)
        summary = response.split("\n")[-1] if "\n" in response else "Let's make today count!"

        return DailyPlan(date=today, tasks=tasks, summary=summary)

    async def create_weekly_plan(self, user_id: str) -> DailyPlan:
        identity = await identity_builder.get_identity(user_id)
        constraints = identity.get("constraints", {}) if identity else {}

        constraints_section = ""
        if any(v is not None for v in constraints.values()):
            parts = []
            if constraints.get("weekly_hours_available") is not None:
                parts.append(f"- Total available hours this week: {constraints['weekly_hours_available']}")
            if constraints.get("monthly_budget") is not None:
                parts.append(f"- Monthly budget: ${constraints['monthly_budget']}")
            if constraints.get("health_limits"):
                parts.append(f"- Health limits: {constraints['health_limits']}")
            if constraints.get("risk_tolerance"):
                parts.append(f"- Risk tolerance: {constraints['risk_tolerance']}")
            constraints_section = "\nConstraints — plan must fit within these:\n" + "\n".join(parts) + "\n"

        prompt = f"""Create a high-level weekly plan with key objectives.
Focus on 3-5 major goals for the week.
{constraints_section}
Format: priority|goal
Example:
high|Complete project milestone
medium|Learn new skill module
low|Organize workspace"""

        response = await self._generate(prompt, task_type=TaskType.GENERATION)
        return DailyPlan(date="This Week", tasks=[], summary=response)

    def _parse_plan(self, response: str) -> list[PlanTask]:
        tasks = []
        for line in response.strip().split("\n"):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 3:
                    # Clean up any markdown formatting
                    title = parts[2].strip().replace("**", "").replace("*", "")
                    time_block = parts[0].strip().replace("**", "").replace("*", "")
                    priority = parts[1].strip().replace("**", "").replace("*", "")
                    tasks.append(PlanTask(title=title, time_block=time_block, priority=priority))
        return tasks
