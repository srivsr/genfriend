from typing import List
from datetime import date
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.opportunity_score import OpportunityScore
from app.models.decision_log import DecisionLog
from app.models.experiment import Experiment
from app.models.distraction_rule import DistractionRule
from .base import BaseRepository


class OpportunityScoreRepository(BaseRepository[OpportunityScore]):
    def __init__(self, db: AsyncSession):
        super().__init__(OpportunityScore, db)

    async def get_by_status(self, user_id: str, status: str) -> List[OpportunityScore]:
        result = await self.db.execute(
            select(OpportunityScore)
            .where(and_(OpportunityScore.user_id == user_id, OpportunityScore.status == status))
            .order_by(OpportunityScore.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_top_scored(self, user_id: str, limit: int = 10) -> List[OpportunityScore]:
        result = await self.db.execute(
            select(OpportunityScore)
            .where(OpportunityScore.user_id == user_id)
            .order_by(OpportunityScore.total_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class DecisionLogRepository(BaseRepository[DecisionLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(DecisionLog, db)

    async def get_pending_reviews(self, user_id: str) -> List[DecisionLog]:
        result = await self.db.execute(
            select(DecisionLog)
            .where(and_(
                DecisionLog.user_id == user_id,
                DecisionLog.status == "pending_review",
                DecisionLog.review_date <= date.today()
            ))
            .order_by(DecisionLog.review_date)
        )
        return list(result.scalars().all())


class ExperimentRepository(BaseRepository[Experiment]):
    def __init__(self, db: AsyncSession):
        super().__init__(Experiment, db)

    async def get_open(self, user_id: str) -> List[Experiment]:
        result = await self.db.execute(
            select(Experiment)
            .where(and_(Experiment.user_id == user_id, Experiment.status == "open"))
            .order_by(Experiment.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_closed(self, user_id: str) -> List[Experiment]:
        result = await self.db.execute(
            select(Experiment)
            .where(and_(Experiment.user_id == user_id, Experiment.status == "closed"))
            .order_by(Experiment.closed_at.desc())
        )
        return list(result.scalars().all())


class DistractionRuleRepository(BaseRepository[DistractionRule]):
    def __init__(self, db: AsyncSession):
        super().__init__(DistractionRule, db)

    async def get_active_rules(self, user_id: str) -> List[DistractionRule]:
        result = await self.db.execute(
            select(DistractionRule)
            .where(and_(DistractionRule.user_id == user_id, DistractionRule.is_active == True))
            .order_by(DistractionRule.created_at.desc())
        )
        return list(result.scalars().all())
