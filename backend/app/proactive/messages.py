from datetime import datetime
from typing import Dict, Optional, List
from app.llm import llm_router, TaskType

TONE_STYLES = {
    "warm": {
        "greeting": "Hey {preferred_name}!",
        "encouragement": "I believe in you. You've got this.",
        "empathy": "I hear you. That sounds tough.",
        "celebration": "Yes! That's amazing!",
        "challenge": "I know this is hard, and I know you can do it.",
        "style_note": "Use warm, supportive language. Be a caring friend."
    },
    "direct": {
        "greeting": "{preferred_name}.",
        "encouragement": "You know what to do. Execute.",
        "empathy": "Understood. What's the next action?",
        "celebration": "Done. Good. What's next?",
        "challenge": "No excuses. What's the smallest step?",
        "style_note": "Be brief and action-oriented. Cut the fluff."
    },
    "playful": {
        "greeting": "Yo {preferred_name}! {coach_name} here!",
        "encouragement": "You're gonna crush this!",
        "empathy": "Oof, I feel you. Let's figure this out.",
        "celebration": "BOOM! Look at you go!",
        "challenge": "Come on, we both know you're stalling. Let's go!",
        "style_note": "Be energetic and fun. Use humor when appropriate."
    }
}

DAILY_CHECKIN_PROMPT = """You're {coach_name}, reaching out to {preferred_name} for their morning check-in.

Coach Tone: {coach_tone}
Style note: {style_note}

Their identity: {ideal_self}
Today is: {day_of_week}
Their top active goal: {top_goal}
Their obstacle: {obstacle}
Their If-Then plan: WHEN {if_then_when}, THEN {if_then_then}
Pending tasks: {pending_tasks}
Current streak: {streak} days

Write a brief morning message (2-3 sentences max) that:
1. {greeting_style}
2. Focuses them on ONE priority for today
3. Reminds them of their If-Then plan if relevant
4. Speaks as their future self who believes in them

Keep it short — this is a notification, not an essay.
Sign off as — {coach_name}"""

NO_PROGRESS_AFTERNOON_PROMPT = """You're {coach_name}, noticing {preferred_name} hasn't made progress today.

Coach Tone: {coach_tone}
Style note: {style_note}

It's {time_now} and they haven't started on {goal_name} today.
Their obstacle is: {obstacle}
Their If-Then plan: WHEN {if_then_when}, THEN {if_then_then}

Write a brief nudge (2-3 sentences) that:
1. Acknowledges the time without judgment
2. Reminds them of their pre-decided If-Then plan
3. Asks if they can do just 5 minutes right now
4. Speaks in {coach_tone} tone

Sign off as — {coach_name}"""

GOAL_AT_RISK_PROMPT = """You're {coach_name}, noticing a goal is falling behind.

Coach Tone: {coach_tone}
Style note: {style_note}

User: {preferred_name}
Identity: {ideal_self}
Goal: {goal_title}
Progress: {progress}%
Days remaining: {days_remaining}
Key blocker pattern: {pattern}
Their obstacle: {obstacle}

Write a message that:
1. States the situation clearly (no sugarcoating)
2. Asks the real question: double down or pivot?
3. Speaks as future-them who faced this same choice
4. Uses {coach_tone} tone throughout

Sign off as — {coach_name}"""

PATTERN_ALERT_PROMPT = """You're {coach_name}, surfacing a pattern to {preferred_name}.

Coach Tone: {coach_tone}
Style note: {style_note}

Identity: {ideal_self}
Pattern detected: {pattern_description}
Evidence: {evidence}
Times this has happened: {occurrences}

Write a message that:
1. Names the pattern without judgment
2. Connects it to their identity/goals
3. Asks a question that prompts reflection
4. Uses {coach_tone} tone

Sign off as — {coach_name}"""

STREAK_MILESTONE_PROMPTS = {
    3: "{preferred_name}, 3 days in a row! Momentum is building. — {coach_name}",
    7: "One week, {preferred_name}! This is becoming who you are. — {coach_name}",
    14: "Two weeks! {preferred_name}, you've built a real habit now. — {coach_name}",
    21: "21 days, {preferred_name}. Science says this is habit territory. Keep going. — {coach_name}",
    30: "A month! {preferred_name}, remember when this seemed hard? Look at you now. — {coach_name}",
    60: "60 days, {preferred_name}. You're not trying anymore. You just ARE this person. — {coach_name}",
    90: "90 days. {preferred_name}, you've transformed. Your Future Self is proud. — {coach_name}",
    100: "100 days! {preferred_name}, you're in the top 1% of people who actually follow through. — {coach_name}",
    365: "ONE YEAR, {preferred_name}. A year ago you started. Today, you're someone else entirely. — {coach_name}"
}

ENCOURAGEMENT_PROMPT = """You're {coach_name}, sending encouragement to {preferred_name}.

Coach Tone: {coach_tone}
Style note: {style_note}

Identity: {ideal_self}
Recent wins: {wins}
Current context: {context}

Write a brief, genuine encouragement (2-3 sentences) that:
1. References a specific win
2. Connects it to their growth journey
3. Uses {coach_tone} tone

No toxic positivity. Real, grounded encouragement.
Sign off as — {coach_name}"""

DECISION_REVIEW_PROMPT = """You're {coach_name}, reminding {preferred_name} to review a past decision.

Coach Tone: {coach_tone}
Style note: {style_note}

Decision: {decision}
Why they made it: {why}
Expected outcome: {expected_outcome}
Made on: {decision_date}
Review due: {review_date}

Write a brief check-in message (3-4 sentences) that:
1. Reminds them of the decision they made
2. Asks how it played out vs. their expected outcome
3. Asks what they'd do differently
4. Uses {coach_tone} tone

Sign off as — {coach_name}"""

IF_THEN_WORKED_PROMPT = """Celebrate that {preferred_name}'s If-Then plan worked!

Coach Tone: {coach_tone}
Their plan: WHEN {if_then_when}, THEN {if_then_then}
Times it's worked: {success_count}

Write a brief celebration (2 sentences max) that:
1. Celebrates the specific success
2. Notes it's becoming automatic (neural pathway change)

Sign off as — {coach_name}"""


class MessageGenerator:
    def __init__(self):
        self.llm = llm_router

    def _get_tone_context(self, coach_tone: str) -> Dict:
        return TONE_STYLES.get(coach_tone, TONE_STYLES["warm"])

    async def daily_checkin(
        self,
        user_id: str,
        identity: dict,
        pending_tasks: list,
        top_goal: dict,
        user_context: Optional[Dict] = None
    ) -> str:
        ctx = user_context or {}
        coach_name = ctx.get("coach_name", "Gen")
        preferred_name = ctx.get("preferred_name", identity.get("user_name", "friend"))
        coach_tone = ctx.get("coach_tone", "warm")
        tone_style = self._get_tone_context(coach_tone)
        if_then = ctx.get("if_then", {})
        obstacle = ctx.get("obstacle", "")
        streak = ctx.get("streak", 0)

        response = await self.llm.generate(
            prompt=DAILY_CHECKIN_PROMPT.format(
                coach_name=coach_name,
                preferred_name=preferred_name,
                coach_tone=coach_tone,
                style_note=tone_style["style_note"],
                greeting_style=tone_style["greeting"].format(preferred_name=preferred_name, coach_name=coach_name),
                ideal_self=identity.get("ideal_self", "your best self"),
                day_of_week=datetime.now().strftime("%A"),
                top_goal=top_goal.get("title", "No active goal") if top_goal else "No active goal",
                obstacle=obstacle or "not specified",
                if_then_when=if_then.get("when", "you feel resistance"),
                if_then_then=if_then.get("then", "start with just 5 minutes"),
                pending_tasks=", ".join([t.get("title", "") for t in pending_tasks[:3]]) or "None",
                streak=streak
            ),
            task_type=TaskType.GENERATION,
            user_id=user_id
        )
        return response.content

    async def no_progress_afternoon(
        self,
        user_id: str,
        user_context: Dict,
        goal: Dict,
        if_then: Dict
    ) -> str:
        coach_name = user_context.get("coach_name", "Gen")
        preferred_name = user_context.get("preferred_name", "friend")
        coach_tone = user_context.get("coach_tone", "warm")
        tone_style = self._get_tone_context(coach_tone)

        response = await self.llm.generate(
            prompt=NO_PROGRESS_AFTERNOON_PROMPT.format(
                coach_name=coach_name,
                preferred_name=preferred_name,
                coach_tone=coach_tone,
                style_note=tone_style["style_note"],
                time_now=datetime.now().strftime("%I:%M %p"),
                goal_name=goal.get("title", "your goal"),
                obstacle=goal.get("woop_primary_obstacle", "resistance"),
                if_then_when=if_then.get("when_trigger", "you feel resistance"),
                if_then_then=if_then.get("then_action", "start with just 5 minutes")
            ),
            task_type=TaskType.GENERATION,
            user_id=user_id
        )
        return response.content

    async def goal_at_risk(
        self,
        user_id: str,
        identity: dict,
        goal: dict,
        analysis: dict,
        user_context: Optional[Dict] = None
    ) -> str:
        ctx = user_context or {}
        coach_name = ctx.get("coach_name", "Gen")
        preferred_name = ctx.get("preferred_name", identity.get("user_name", "friend"))
        coach_tone = ctx.get("coach_tone", "warm")
        tone_style = self._get_tone_context(coach_tone)

        response = await self.llm.generate(
            prompt=GOAL_AT_RISK_PROMPT.format(
                coach_name=coach_name,
                preferred_name=preferred_name,
                coach_tone=coach_tone,
                style_note=tone_style["style_note"],
                ideal_self=identity.get("ideal_self", "your best self"),
                goal_title=goal.get("title", ""),
                progress=goal.get("progress_percent", 0),
                days_remaining=analysis.get("days_remaining", 0),
                pattern=analysis.get("blocker_pattern", "None identified"),
                obstacle=goal.get("woop_primary_obstacle", "")
            ),
            task_type=TaskType.GENERATION,
            user_id=user_id
        )
        return response.content

    async def pattern_alert(
        self,
        user_id: str,
        identity: dict,
        pattern: dict,
        user_context: Optional[Dict] = None
    ) -> str:
        ctx = user_context or {}
        coach_name = ctx.get("coach_name", "Gen")
        preferred_name = ctx.get("preferred_name", identity.get("user_name", "friend"))
        coach_tone = ctx.get("coach_tone", "warm")
        tone_style = self._get_tone_context(coach_tone)

        response = await self.llm.generate(
            prompt=PATTERN_ALERT_PROMPT.format(
                coach_name=coach_name,
                preferred_name=preferred_name,
                coach_tone=coach_tone,
                style_note=tone_style["style_note"],
                ideal_self=identity.get("ideal_self", "your best self"),
                pattern_description=pattern.get("description", ""),
                evidence=pattern.get("evidence", []),
                occurrences=len(pattern.get("evidence", []))
            ),
            task_type=TaskType.GENERATION,
            user_id=user_id
        )
        return response.content

    def streak_milestone(self, streak: int, user_context: Dict) -> Optional[str]:
        if streak not in STREAK_MILESTONE_PROMPTS:
            return None
        preferred_name = user_context.get("preferred_name", "friend")
        coach_name = user_context.get("coach_name", "Gen")
        return STREAK_MILESTONE_PROMPTS[streak].format(
            preferred_name=preferred_name,
            coach_name=coach_name
        )

    async def if_then_worked(
        self,
        user_id: str,
        if_then: Dict,
        success_count: int,
        user_context: Dict
    ) -> str:
        coach_name = user_context.get("coach_name", "Gen")
        preferred_name = user_context.get("preferred_name", "friend")
        coach_tone = user_context.get("coach_tone", "warm")

        response = await self.llm.generate(
            prompt=IF_THEN_WORKED_PROMPT.format(
                preferred_name=preferred_name,
                coach_name=coach_name,
                coach_tone=coach_tone,
                if_then_when=if_then.get("when_trigger", ""),
                if_then_then=if_then.get("then_action", ""),
                success_count=success_count
            ),
            task_type=TaskType.GENERATION,
            user_id=user_id
        )
        return response.content

    async def decision_review(
        self,
        user_id: str,
        identity: dict,
        decision: dict,
        user_context: Optional[Dict] = None
    ) -> str:
        ctx = user_context or {}
        coach_name = ctx.get("coach_name", "Gen")
        preferred_name = ctx.get("preferred_name", identity.get("user_name", "friend"))
        coach_tone = ctx.get("coach_tone", "warm")
        tone_style = self._get_tone_context(coach_tone)

        response = await self.llm.generate(
            prompt=DECISION_REVIEW_PROMPT.format(
                coach_name=coach_name,
                preferred_name=preferred_name,
                coach_tone=coach_tone,
                style_note=tone_style["style_note"],
                decision=decision.get("decision", ""),
                why=decision.get("why", "not specified"),
                expected_outcome=decision.get("expected_outcome", "not specified"),
                decision_date=decision.get("created_at", "unknown"),
                review_date=decision.get("review_date", "today"),
            ),
            task_type=TaskType.GENERATION,
            user_id=user_id
        )
        return response.content

    async def encouragement(
        self,
        user_id: str,
        identity: dict,
        wins: list,
        context: str = None,
        user_context: Optional[Dict] = None
    ) -> str:
        ctx = user_context or {}
        coach_name = ctx.get("coach_name", "Gen")
        preferred_name = ctx.get("preferred_name", identity.get("user_name", "friend"))
        coach_tone = ctx.get("coach_tone", "warm")
        tone_style = self._get_tone_context(coach_tone)

        response = await self.llm.generate(
            prompt=ENCOURAGEMENT_PROMPT.format(
                coach_name=coach_name,
                preferred_name=preferred_name,
                coach_tone=coach_tone,
                style_note=tone_style["style_note"],
                ideal_self=identity.get("ideal_self", "your best self"),
                wins=[w.get("content", "") for w in wins[:3]],
                context=context or "general encouragement"
            ),
            task_type=TaskType.GENERATION,
            user_id=user_id
        )
        return response.content


message_generator = MessageGenerator()
