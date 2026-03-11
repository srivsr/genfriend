from dataclasses import dataclass
from typing import Optional
from app.llm import llm_router, TaskType
from app.core.database import async_session
from app.repositories.journal_repository import JournalRepository
from app.repositories.goal_repository import GoalRepository


@dataclass
class JournalEntry:
    entry_type: str
    content: str
    enrichment: Optional[str] = None
    related_goal_id: Optional[str] = None
    mood: Optional[str] = None
    energy_level: Optional[int] = None


ENRICH_WIN_PROMPT = """A user just logged a win:

Win: {content}
User's identity: {identity}
Related goal: {goal}

Provide a brief (1-2 sentences) enrichment that:
1. Connects this win to their journey toward becoming {ideal_self}
2. Names the specific attribute/skill they demonstrated
3. Is encouraging but not over-the-top

Example: "This shows you're developing the customer focus that defines great CEOs. You took action even when it was uncomfortable." """

RECALL_WINS_PROMPT = """The user is struggling. Find wins from their history that are relevant to encourage them.

Current situation: {context}
User's identity: {identity}
Available wins: {wins}

Select 1-2 wins that directly relate to what they're facing now.
For each, explain WHY it's relevant: "Remember when you [specific win]? That same [skill/courage/persistence] applies here."

Keep it brief and personal."""


class JournalKeeper:
    def __init__(self):
        self.llm = llm_router

    async def capture_win(self, user_id: str, content: str, related_goal_id: Optional[str] = None, identity: dict = None) -> JournalEntry:
        goal = await self._get_goal(related_goal_id) if related_goal_id else None

        enrichment = None
        if identity:
            response = await self.llm.generate(
                prompt=ENRICH_WIN_PROMPT.format(
                    content=content,
                    identity=identity,
                    goal=goal,
                    ideal_self=identity.get("ideal_self", "your best self")
                ),
                task_type=TaskType.GENERATION,
                user_id=user_id
            )
            enrichment = response.content

        return JournalEntry(
            entry_type="win",
            content=content,
            enrichment=enrichment,
            related_goal_id=related_goal_id
        )

    async def capture_moment(self, user_id: str, content: str, mood: Optional[str] = None, energy_level: Optional[int] = None) -> JournalEntry:
        return JournalEntry(
            entry_type="moment",
            content=content,
            mood=mood,
            energy_level=energy_level
        )

    async def recall_relevant_wins(self, user_id: str, current_context: str, identity: dict = None) -> str:
        wins = await self.get_recent_wins(user_id, limit=10)

        if not wins:
            return "You haven't logged any wins yet. Every small victory counts - start capturing them!"

        response = await self.llm.generate(
            prompt=RECALL_WINS_PROMPT.format(
                context=current_context,
                identity=identity or {},
                wins=[w.get("content", "") for w in wins]
            ),
            task_type=TaskType.GENERATION,
            user_id=user_id
        )

        return response.content

    async def get_recent_wins(self, user_id: str, limit: int = 5) -> list:
        async with async_session() as db:
            repo = JournalRepository(db)
            wins = await repo.get_wins(user_id)
            return [
                {
                    "id": w.id,
                    "content": w.content,
                    "enrichment": w.enrichment,
                    "related_goal_id": w.related_goal_id,
                    "created_at": w.created_at.isoformat() if w.created_at else None
                }
                for w in wins[:limit]
            ]

    async def get_wins_for_goal(self, goal_id: str) -> list:
        async with async_session() as db:
            repo = JournalRepository(db)
            entries = await repo.get_by_goal(goal_id)
            wins = [e for e in entries if e.entry_type == "win"]
            return [
                {
                    "id": w.id,
                    "content": w.content,
                    "enrichment": w.enrichment,
                    "created_at": w.created_at.isoformat() if w.created_at else None
                }
                for w in wins
            ]

    async def _get_goal(self, goal_id: str) -> Optional[dict]:
        async with async_session() as db:
            repo = GoalRepository(db)
            goal = await repo.get_by_id(goal_id)
            if not goal:
                return None
            return {
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "progress_percent": goal.progress_percent
            }


journal_keeper = JournalKeeper()
