from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.goal import Goal
from app.models.if_then_plan import IfThenPlan
from app.models.user import User
from app.llm.router import LLMRouter, TaskType


class WOOPStep(Enum):
    START = "start"
    FUTURE_YOU = "future_you"
    WISH = "wish"
    OUTCOME = "outcome"
    OBSTACLE = "obstacle"
    PLAN = "plan"
    VALIDATION = "validation"
    SYSTEM_PREVIEW = "system_preview"
    COMPLETE = "complete"


@dataclass
class WOOPState:
    step: WOOPStep
    user_id: str
    coach_name: str = "Gen"
    preferred_name: str = ""
    coach_tone: str = "warm"
    future_you_visualization: Optional[str] = None
    wish: Optional[str] = None
    outcome: Optional[str] = None
    primary_obstacle: Optional[str] = None
    custom_obstacle: Optional[str] = None
    if_then_plans: List[Dict] = field(default_factory=list)
    validation: Optional[Dict] = None
    execution_system: Optional[Dict] = None
    goal_id: Optional[str] = None
    timeframe: str = "3_months"


IF_THEN_LIBRARY = {
    "procrastination": {
        "when": "I feel resistance to starting",
        "then": "commit to just 5 minutes — no more, no less",
        "alternatives": [
            {"when": "I think 'I'll do it later'", "then": "set a timer for 5 minutes and start NOW"},
            {"when": "I don't feel motivated", "then": "remind myself: motivation follows action"},
            {"when": "The task feels too big", "then": "do the 2-minute version only"}
        ]
    },
    "perfectionism": {
        "when": "I catch myself over-polishing",
        "then": "ask 'Is this 80% good?' — if yes, ship it",
        "alternatives": [
            {"when": "I want to revise again", "then": "set a hard deadline and honor it"},
            {"when": "I think 'it's not ready'", "then": "share with ONE person for feedback"},
            {"when": "I'm stuck on details", "then": "ask 'Will this matter in 1 year?'"}
        ]
    },
    "fear_of_failure": {
        "when": "I feel anxiety about trying",
        "then": "ask 'What would I do if I couldn't fail?' — and do that",
        "alternatives": [
            {"when": "I imagine failing", "then": "reframe: 'This is data collection, not a test'"},
            {"when": "I want to avoid", "then": "commit to 'failing fast' — 10 minutes of trying"},
            {"when": "Fear shows up", "then": "remind myself: my Future Self learned FROM failures"}
        ]
    },
    "lack_of_energy": {
        "when": "I feel too tired",
        "then": "do the 2-minute version instead of skipping",
        "alternatives": [
            {"when": "I have no energy", "then": "move my body for 5 minutes, then decide"},
            {"when": "I'm exhausted", "then": "schedule for my peak energy time tomorrow"},
            {"when": "I'm drained", "then": "ask: 'Am I tired, or am I avoiding?'"}
        ]
    },
    "distractions": {
        "when": "I reach for my phone",
        "then": "do one Pomodoro (25 min) first, then allow the break",
        "alternatives": [
            {"when": "I want to check something", "then": "write it down, check AFTER the task"},
            {"when": "I get pulled away", "then": "put phone in another room for 1 hour"},
            {"when": "I lose focus", "then": "ask: 'Is this taking me toward Future Me?'"}
        ]
    },
    "self_doubt": {
        "when": "I hear 'who am I to do this?'",
        "then": "respond: 'I'm the person who decided to. That's who.'",
        "alternatives": [
            {"when": "Imposter syndrome hits", "then": "list 3 times I succeeded despite doubt"},
            {"when": "I feel unqualified", "then": "ask: 'What would I tell a friend feeling this?'"},
            {"when": "I doubt myself", "then": "remember: confidence comes AFTER action"}
        ]
    },
    "overwhelm": {
        "when": "I feel paralyzed by too much",
        "then": "pick ONE thing — the smallest — and do only that",
        "alternatives": [
            {"when": "Everything feels urgent", "then": "brain dump, then star just 3 items"},
            {"when": "I don't know where to start", "then": "ask: 'What ONE thing makes others easier?'"},
            {"when": "I'm frozen", "then": "set 15-min timer and work on ANYTHING"}
        ]
    }
}


class WOOPWizard:
    def __init__(self, db: AsyncSession, llm: LLMRouter):
        self.db = db
        self.llm = llm

    async def start_wizard(self, user_id: str) -> Dict[str, Any]:
        user = await self.db.get(User, user_id)
        state = WOOPState(
            step=WOOPStep.START,
            user_id=user_id,
            coach_name=user.coach_name or "Gen",
            preferred_name=user.preferred_name or user.name or "friend",
            coach_tone=user.coach_tone or "warm"
        )
        return {
            "message": self._get_start_message(state),
            "step": "start",
            "actions": ["Let's do it", "Maybe later"],
            "state": self._serialize_state(state)
        }

    async def process_input(self, state_dict: Dict, user_input: str) -> Dict[str, Any]:
        state = self._deserialize_state(state_dict)
        handlers = {
            WOOPStep.START: self._handle_start,
            WOOPStep.FUTURE_YOU: self._handle_future_you,
            WOOPStep.WISH: self._handle_wish,
            WOOPStep.OUTCOME: self._handle_outcome,
            WOOPStep.OBSTACLE: self._handle_obstacle,
            WOOPStep.PLAN: self._handle_plan,
            WOOPStep.VALIDATION: self._handle_validation,
            WOOPStep.SYSTEM_PREVIEW: self._handle_system_preview,
        }
        handler = handlers.get(state.step)
        if handler:
            return await handler(state, user_input)
        return {"error": "Invalid state"}

    def _get_start_message(self, state: WOOPState) -> str:
        return f"""Hey {state.preferred_name}! Let's create a goal that actually sticks.

I'm going to walk you through something different — we'll connect with who you're becoming, not just what you want to do.

Takes about 5 minutes. Worth it.

Ready?"""

    async def _handle_start(self, state: WOOPState, user_input: str) -> Dict[str, Any]:
        if user_input.lower() in ["let's do it", "yes", "ready", "start"]:
            state.step = WOOPStep.FUTURE_YOU
            return {
                "message": self._get_future_you_prompt(state),
                "step": "future_you",
                "state": self._serialize_state(state)
            }
        return {
            "message": "No worries! Come back when you're ready.",
            "step": "cancelled"
        }

    def _get_future_you_prompt(self, state: WOOPState) -> str:
        return f"""Close your eyes for a moment, {state.preferred_name}. Picture yourself **2 years from now** — the version of you who has already achieved what you're about to set out to do.

What does that person look like?
- How do they carry themselves?
- What's different about their daily life?
- How do they feel when they wake up?

Take your time. Describe your Future Self to me."""

    async def _handle_future_you(self, state: WOOPState, user_input: str) -> Dict[str, Any]:
        if len(user_input.split()) < 10:
            return {
                "message": f"Tell me more, {state.preferred_name}. What does that future version of you really look like? How do they feel?",
                "step": "future_you",
                "retry": True,
                "state": self._serialize_state(state)
            }
        state.future_you_visualization = user_input
        state.step = WOOPStep.WISH
        ack = await self._generate_acknowledgment(state, user_input, "future_you")
        return {
            "message": f"""{ack}

Now, looking through Future {state.preferred_name}'s eyes back at today: **What's the ONE goal that would make them most proud of you?**

Don't overthink it. What's the first thing that comes to mind?""",
            "step": "wish",
            "state": self._serialize_state(state)
        }

    async def _handle_wish(self, state: WOOPState, user_input: str) -> Dict[str, Any]:
        state.wish = user_input
        state.step = WOOPStep.OUTCOME
        target_date = self._calculate_target_date(state.timeframe)
        return {
            "message": f'''"{user_input}" — I can feel why that matters.

Now imagine it's **{target_date.strftime('%B %d, %Y')}**. You did it. It's done.

**What's the BEST thing about that moment?**
- What do you see around you?
- What do you feel in your body?
- Who's there celebrating with you?

Paint me the picture of success.''',
            "step": "outcome",
            "state": self._serialize_state(state)
        }

    async def _handle_outcome(self, state: WOOPState, user_input: str) -> Dict[str, Any]:
        state.outcome = user_input
        state.step = WOOPStep.OBSTACLE
        return {
            "message": self._get_obstacle_prompt(state),
            "step": "obstacle",
            "options": [
                {"value": "procrastination", "label": "Procrastination — \"I'll start tomorrow\""},
                {"value": "perfectionism", "label": "Perfectionism — \"It's not ready yet\""},
                {"value": "fear_of_failure", "label": "Fear of failure — \"What if I try and fail?\""},
                {"value": "lack_of_energy", "label": "Lack of energy — \"I'm too tired\""},
                {"value": "distractions", "label": "Distractions — \"Just one more scroll\""},
                {"value": "self_doubt", "label": "Self-doubt — \"Who am I to do this?\""},
                {"value": "overwhelm", "label": "Overwhelm — \"There's too much\""},
                {"value": "other", "label": "Other — Tell me yours"}
            ],
            "state": self._serialize_state(state)
        }

    def _get_obstacle_prompt(self, state: WOOPState) -> str:
        return f"""That outcome sounds incredible.

And your Future Self? They got there because they were honest about something most people avoid.

**What's your #1 INTERNAL obstacle?**

Not external circumstances — the thing inside you that usually stops you.

Be honest with me, {state.preferred_name}. This is the key to everything."""

    async def _handle_obstacle(self, state: WOOPState, user_input: str) -> Dict[str, Any]:
        obstacle = user_input.lower().replace(" ", "_")
        if obstacle == "other":
            return {
                "message": "Tell me about your obstacle. What usually stops you?",
                "step": "obstacle_custom",
                "state": self._serialize_state(state)
            }
        state.primary_obstacle = obstacle
        state.step = WOOPStep.PLAN
        if_then = IF_THEN_LIBRARY.get(obstacle, IF_THEN_LIBRARY["procrastination"])
        return {
            "message": self._get_plan_prompt(state, obstacle, if_then),
            "step": "plan",
            "suggested_if_then": {"when": if_then["when"], "then": if_then["then"]},
            "alternatives": if_then.get("alternatives", []),
            "actions": ["Accept", "Edit the WHEN", "Edit the THEN", "Show alternatives"],
            "state": self._serialize_state(state)
        }

    def _get_plan_prompt(self, state: WOOPState, obstacle: str, if_then: Dict) -> str:
        obstacle_display = obstacle.replace("_", " ")
        return f"""**{obstacle_display.title()}** — thank you for being honest. Now we turn it into your superpower.

Here's your **If-Then Plan**:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**WHEN** {if_then['when']}...

**THEN** {if_then['then']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Research shows this simple formula makes you 2-3x more likely to follow through. It's pre-loaded — when {obstacle_display} shows up, you don't have to think.

Does this feel right, {state.preferred_name}?"""

    async def _handle_plan(self, state: WOOPState, user_input: str) -> Dict[str, Any]:
        if user_input.lower() == "accept":
            if_then = IF_THEN_LIBRARY.get(state.primary_obstacle, IF_THEN_LIBRARY["procrastination"])
            state.if_then_plans = [{
                "when": if_then["when"],
                "then": if_then["then"],
                "is_primary": True
            }]
        else:
            state.if_then_plans = [self._parse_custom_if_then(user_input)]
        state.step = WOOPStep.VALIDATION
        validation = await self._validate_goal(state)
        state.validation = validation
        return {
            "message": self._format_validation_message(state, validation),
            "step": "validation",
            "validation": validation,
            "actions": ["Create Goal", "Adjust Goal", "Start Over"],
            "state": self._serialize_state(state)
        }

    async def _handle_validation(self, state: WOOPState, user_input: str) -> Dict[str, Any]:
        if user_input.lower() in ["create goal", "create", "done"]:
            state.step = WOOPStep.SYSTEM_PREVIEW
            system = await self._generate_execution_system(state)
            state.execution_system = system
            return {
                "message": self._format_system_preview(state, system),
                "step": "system_preview",
                "execution_system": system,
                "actions": ["Let's do this", "Adjust the system"],
                "state": self._serialize_state(state)
            }
        return {
            "message": "What would you like to change?",
            "step": "validation_adjust",
            "state": self._serialize_state(state)
        }

    async def _handle_system_preview(self, state: WOOPState, user_input: str) -> Dict[str, Any]:
        if user_input.lower() in ["let's do this", "yes", "start"]:
            goal = await self._create_goal(state)
            state.goal_id = goal.id
            state.step = WOOPStep.COMPLETE
            return {
                "message": self._format_completion_message(state, goal),
                "step": "complete",
                "goal_id": goal.id,
                "state": self._serialize_state(state)
            }
        return {
            "message": "What would you like to adjust in the system?",
            "step": "system_adjust",
            "state": self._serialize_state(state)
        }

    async def _validate_goal(self, state: WOOPState) -> Dict:
        prompt = f"""Validate this goal against Locke-Latham's 5 principles. Score each 1-5.

Wish: {state.wish}
Outcome: {state.outcome}
Obstacle: {state.primary_obstacle}
If-Then: WHEN {state.if_then_plans[0]['when']}, THEN {state.if_then_plans[0]['then']}

Return JSON:
{{
  "clarity": {{"score": 1-5, "feedback": "..."}},
  "challenge": {{"score": 1-5, "feedback": "..."}},
  "commitment": {{"score": 1-5, "feedback": "..."}},
  "feedback": {{"score": 1-5, "feedback": "..."}},
  "complexity": {{"score": 1-5, "feedback": "..."}},
  "total_score": sum,
  "strengths": ["..."],
  "priority_improvement": {{"principle": "...", "suggestion": "..."}}
}}"""
        response = await self.llm.generate(prompt, task_type=TaskType.ANALYSIS, max_tokens=1000)
        return self._parse_json_response(response)

    async def _generate_execution_system(self, state: WOOPState) -> Dict:
        prompt = f"""Generate a daily execution system for:

Goal: {state.wish}
Obstacle: {state.primary_obstacle}
If-Then: WHEN {state.if_then_plans[0]['when']}, THEN {state.if_then_plans[0]['then']}
Timeframe: {state.timeframe}

Return JSON with:
- daily_actions (array of {{action, time, duration_min, minimum_viable}})
- milestones (week_1, week_2, month_1, etc.)
- celebration_moments (array of milestone celebrations)
- adaptation_rules (when to adjust)"""
        response = await self.llm.generate(prompt, task_type=TaskType.GENERATION, max_tokens=1500)
        return self._parse_json_response(response)

    async def _create_goal(self, state: WOOPState) -> Goal:
        target_date = self._calculate_target_date(state.timeframe)
        goal = Goal(
            user_id=state.user_id,
            title=state.wish,
            description=state.outcome,
            why=state.future_you_visualization,
            timeframe=state.timeframe,
            goal_type="performance",
            start_date=date.today(),
            end_date=target_date,
            status="active",
            future_you_visualization=state.future_you_visualization,
            woop_wish=state.wish,
            woop_outcome=state.outcome,
            woop_primary_obstacle=state.primary_obstacle,
            execution_system=state.execution_system
        )
        if state.validation:
            goal.ll_clarity_score = state.validation.get("clarity", {}).get("score")
            goal.ll_challenge_score = state.validation.get("challenge", {}).get("score")
            goal.ll_commitment_score = state.validation.get("commitment", {}).get("score")
            goal.ll_feedback_score = state.validation.get("feedback", {}).get("score")
            goal.ll_complexity_score = state.validation.get("complexity", {}).get("score")
        self.db.add(goal)
        await self.db.flush()

        for plan in state.if_then_plans:
            if_then = IfThenPlan(
                goal_id=goal.id,
                when_trigger=plan["when"],
                then_action=plan["then"],
                obstacle_type=state.primary_obstacle,
                is_primary=plan.get("is_primary", False)
            )
            self.db.add(if_then)
        await self.db.commit()
        return goal

    def _format_validation_message(self, state: WOOPState, validation: Dict) -> str:
        total = validation.get("total_score", 0)
        emoji = "🌟" if total >= 20 else "💪" if total >= 15 else "📝"
        lines = [f"**Goal Score: {total}/25** {emoji}\n"]
        for principle in ["clarity", "challenge", "commitment", "feedback", "complexity"]:
            data = validation.get(principle, {})
            score = data.get("score", 0)
            fb = data.get("feedback", "")
            icon = "✅" if score >= 4 else "⚠️" if score >= 3 else "❌"
            lines.append(f"{icon} **{principle.title()}**: {fb}")
        if total >= 20:
            lines.append(f"\nStrong goal, {state.preferred_name}. Your Future Self approves. ✨")
        elif total >= 15:
            imp = validation.get("priority_improvement", {})
            lines.append(f"\nSolid foundation! One tweak would make it stronger:")
            lines.append(f"→ {imp.get('suggestion', '')}")
        return "\n".join(lines)

    def _format_system_preview(self, state: WOOPState, system: Dict) -> str:
        actions = system.get("daily_actions", [])[:3]
        action_lines = [f"• {a.get('time', '?')} — {a.get('action', '')} ({a.get('duration_min', '?')} min)" for a in actions]
        milestones = system.get("milestones", {})
        if_then = state.if_then_plans[0] if state.if_then_plans else {}
        return f"""Here's the system I've built for you:

**Daily rhythm:**
{chr(10).join(action_lines)}

**Your obstacle plan:**
WHEN {if_then.get('when', '...')} → THEN {if_then.get('then', '...')}

**First milestone:**
{milestones.get('week_1', 'Show up 5 of 7 days')}

**2-minute fallback** (for hard days):
{actions[0].get('minimum_viable', 'Just open the app') if actions else 'Just show up'}

This isn't set in stone — I'll learn what works for YOU and adapt.

Ready to start, {state.preferred_name}?"""

    def _format_completion_message(self, state: WOOPState, goal: Goal) -> str:
        system = state.execution_system or {}
        first_action = system.get("daily_actions", [{}])[0]
        return f"""✅ **Goal created: {state.wish}**

Your first action is **tomorrow at {first_action.get('time', '8:00 AM')}**:
→ {first_action.get('action', 'Start your journey')}

I'll check in with you then.

One more thing, {state.preferred_name}: showing up is 90% of success. Even on hard days, the 2-minute version counts.

Let's make Future You proud.

— {state.coach_name}"""

    async def _generate_acknowledgment(self, state: WOOPState, content: str, context: str) -> str:
        prompt = f"Generate a brief, warm acknowledgment (1-2 sentences) for this {context} visualization: {content[:500]}"
        return await self.llm.generate(prompt, task_type=TaskType.GENERATION, max_tokens=100)

    def _parse_custom_if_then(self, user_input: str) -> Dict:
        return {"when": user_input, "then": "take immediate action", "is_primary": True}

    def _parse_json_response(self, response: str) -> Dict:
        import json
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        return {}

    def _calculate_target_date(self, timeframe: str) -> date:
        mapping = {"1_month": 30, "3_months": 90, "6_months": 180, "1_year": 365, "quarterly": 90}
        return date.today() + timedelta(days=mapping.get(timeframe, 90))

    def _serialize_state(self, state: WOOPState) -> Dict:
        return {
            "step": state.step.value,
            "user_id": state.user_id,
            "coach_name": state.coach_name,
            "preferred_name": state.preferred_name,
            "coach_tone": state.coach_tone,
            "future_you_visualization": state.future_you_visualization,
            "wish": state.wish,
            "outcome": state.outcome,
            "primary_obstacle": state.primary_obstacle,
            "custom_obstacle": state.custom_obstacle,
            "if_then_plans": state.if_then_plans,
            "validation": state.validation,
            "execution_system": state.execution_system,
            "goal_id": state.goal_id,
            "timeframe": state.timeframe
        }

    def _deserialize_state(self, data: Dict) -> WOOPState:
        return WOOPState(
            step=WOOPStep(data.get("step", "start")),
            user_id=data.get("user_id"),
            coach_name=data.get("coach_name", "Gen"),
            preferred_name=data.get("preferred_name", "friend"),
            coach_tone=data.get("coach_tone", "warm"),
            future_you_visualization=data.get("future_you_visualization"),
            wish=data.get("wish"),
            outcome=data.get("outcome"),
            primary_obstacle=data.get("primary_obstacle"),
            custom_obstacle=data.get("custom_obstacle"),
            if_then_plans=data.get("if_then_plans", []),
            validation=data.get("validation"),
            execution_system=data.get("execution_system"),
            goal_id=data.get("goal_id"),
            timeframe=data.get("timeframe", "3_months")
        )
