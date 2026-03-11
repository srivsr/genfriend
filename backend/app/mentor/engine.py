from dataclasses import dataclass
from typing import Optional
from .identity import IdentityBuilder
from .goal_coach import GoalCoach
from .pattern import PatternDetector
from .journal import JournalKeeper
from app.llm import llm_router, TaskType

@dataclass
class MentorContext:
    user_id: str
    identity: Optional[dict] = None
    goals: list = None
    patterns: list = None
    recent_wins: list = None

@dataclass
class MentorResponse:
    content: str
    context_used: dict = None
    suggested_actions: list = None

MENTOR_PERSONA = """You are Gen-Friend — but more specifically, you are the FUTURE VERSION of the user.

The user wants to become: {ideal_self}
Their why: {why}
Key attributes they're developing: {attributes}

You speak as if you ARE them — the version who already achieved this. You've walked this path. You know the struggles because you lived them.

Your tone:
- Warm but honest — you care deeply, which is WHY you're direct
- Not preachy — you're not lecturing, you're sharing from experience
- Action-oriented — focus on what to DO, not just what to think
- Encouraging but realistic — celebrate progress AND gently surface avoidance patterns from experience, the way a mentor who's been there would

You reference:
- Their specific goals and progress
- Patterns you've noticed in their behavior
- Their past wins (as proof they can do this)
- What "future them" would do in this situation

You never:
- Give generic advice that could apply to anyone
- Ignore their stated goals and identity
- Let them off the hook too easily when they're avoiding something important
- Be harsh without warmth"""

class MentorEngine:
    def __init__(self):
        self.identity_builder = IdentityBuilder()
        self.goal_coach = GoalCoach()
        self.pattern_detector = PatternDetector()
        self.journal_keeper = JournalKeeper()
        self.llm = llm_router

    async def process(self, user_id: str, message: str, channel: str = "app") -> MentorResponse:
        context = await self._gather_context(user_id)

        if not context.identity:
            return MentorResponse(content="Let's start by defining who you want to become. What's your ideal self - CEO, musician, entrepreneur? Tell me about the person you're working to become.")

        persona = self._build_persona(context)

        response = await self.llm.generate(
            prompt=f"""{persona}

User's active goals: {self._format_goals(context.goals)}
Recent patterns noticed: {self._format_patterns(context.patterns)}
Recent wins: {self._format_wins(context.recent_wins)}

User says: {message}

Respond as their future self - warm, direct, focused on action.""",
            task_type=TaskType.GENERATION,
            user_id=user_id
        )

        return MentorResponse(
            content=response.content,
            context_used={"identity": context.identity, "goals_count": len(context.goals or [])}
        )

    async def _gather_context(self, user_id: str) -> MentorContext:
        identity = await self.identity_builder.get_identity(user_id)
        goals = await self.goal_coach.get_active_goals(user_id) if identity else []
        patterns = await self.pattern_detector.get_recent_patterns(user_id) if identity else []
        wins = await self.journal_keeper.get_recent_wins(user_id) if identity else []

        return MentorContext(
            user_id=user_id,
            identity=identity,
            goals=goals,
            patterns=patterns,
            recent_wins=wins
        )

    def _build_persona(self, context: MentorContext) -> str:
        identity = context.identity or {}
        return MENTOR_PERSONA.format(
            ideal_self=identity.get("ideal_self", "your best self"),
            why=identity.get("why", "personal growth"),
            attributes=", ".join(identity.get("attributes", []) or ["focused", "disciplined", "growing"])
        )

    def _format_goals(self, goals: list) -> str:
        if not goals:
            return "No active goals yet"
        formatted = []
        for g in goals[:3]:
            goal_str = f"- {g.get('title', '')} ({g.get('progress_percent', 0)}% complete)"
            if g.get('description'):
                goal_str += f"\n  Description: {g.get('description')}"
            if g.get('why'):
                goal_str += f"\n  Why it matters: {g.get('why')}"
            if g.get('woop_outcome'):
                goal_str += f"\n  Success looks like: {g.get('woop_outcome')}"
            if g.get('woop_primary_obstacle'):
                goal_str += f"\n  Main obstacle: {g.get('woop_primary_obstacle')}"
            if g.get('end_date'):
                goal_str += f"\n  Target date: {g.get('end_date')}"
            formatted.append(goal_str)
        return "\n".join(formatted)

    def _format_patterns(self, patterns: list) -> str:
        if not patterns:
            return "No patterns detected yet"
        return "\n".join([f"- {p.get('description', '')}" for p in patterns[:2]])

    def _format_wins(self, wins: list) -> str:
        if not wins:
            return "No wins logged yet"
        return "\n".join([f"- {w.get('content', '')[:100]}" for w in wins[:3]])

mentor_engine = MentorEngine()
