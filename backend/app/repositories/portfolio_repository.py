from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.portfolio import Portfolio, InterviewSession, InterviewMessage
from .base import BaseRepository


class PortfolioRepository(BaseRepository[Portfolio]):
    def __init__(self, db: AsyncSession):
        super().__init__(Portfolio, db)

    async def get_by_user(self, user_id: str) -> Optional[Portfolio]:
        result = await self.db.execute(
            select(Portfolio).where(Portfolio.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Portfolio]:
        result = await self.db.execute(
            select(Portfolio).where(and_(Portfolio.public_slug == slug, Portfolio.is_public == True))
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: str) -> Portfolio:
        existing = await self.get_by_user(user_id)
        if existing:
            return existing
        return await self.create(user_id=user_id)

    async def update_public_settings(
        self,
        portfolio_id: str,
        is_public: bool,
        slug: str = None
    ) -> Optional[Portfolio]:
        portfolio = await self.get_by_id(portfolio_id)
        if portfolio:
            portfolio.is_public = is_public
            if slug:
                portfolio.public_slug = slug
            await self.db.commit()
            await self.db.refresh(portfolio)
        return portfolio

    async def enable_interview(
        self,
        portfolio_id: str,
        intro: str = None,
        topics: List[str] = None
    ) -> Optional[Portfolio]:
        portfolio = await self.get_by_id(portfolio_id)
        if portfolio:
            portfolio.interview_enabled = True
            if intro:
                portfolio.interview_intro = intro
            if topics:
                portfolio.interview_topics = topics
            await self.db.commit()
            await self.db.refresh(portfolio)
        return portfolio


class InterviewSessionRepository(BaseRepository[InterviewSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(InterviewSession, db)

    async def get_by_portfolio(self, portfolio_id: str) -> List[InterviewSession]:
        result = await self.db.execute(
            select(InterviewSession)
            .where(InterviewSession.portfolio_id == portfolio_id)
            .order_by(InterviewSession.started_at.desc())
        )
        return list(result.scalars().all())

    async def get_completed(self, portfolio_id: str) -> List[InterviewSession]:
        result = await self.db.execute(
            select(InterviewSession)
            .where(and_(
                InterviewSession.portfolio_id == portfolio_id,
                InterviewSession.is_completed == True
            ))
            .order_by(InterviewSession.started_at.desc())
        )
        return list(result.scalars().all())

    async def start_session(
        self,
        portfolio_id: str,
        interviewer_name: str = None,
        interviewer_company: str = None,
        interviewer_email: str = None,
        session_type: str = "general"
    ) -> InterviewSession:
        return await self.create(
            portfolio_id=portfolio_id,
            interviewer_name=interviewer_name,
            interviewer_company=interviewer_company,
            interviewer_email=interviewer_email,
            session_type=session_type,
            questions_asked=[],
            topics_discussed=[]
        )

    async def end_session(
        self,
        session_id: str,
        rating: str = None,
        feedback: str = None
    ) -> Optional[InterviewSession]:
        session = await self.get_by_id(session_id)
        if session:
            session.is_completed = True
            session.ended_at = datetime.utcnow()
            if rating:
                session.rating = rating
            if feedback:
                session.feedback = feedback
            await self.db.commit()
            await self.db.refresh(session)
        return session

    async def update_topics(
        self,
        session_id: str,
        question: str,
        topic: str
    ) -> Optional[InterviewSession]:
        session = await self.get_by_id(session_id)
        if session:
            questions = session.questions_asked or []
            questions.append(question)
            session.questions_asked = questions

            topics = session.topics_discussed or []
            if topic not in topics:
                topics.append(topic)
            session.topics_discussed = topics

            await self.db.commit()
            await self.db.refresh(session)
        return session


class InterviewMessageRepository(BaseRepository[InterviewMessage]):
    def __init__(self, db: AsyncSession):
        super().__init__(InterviewMessage, db)

    async def get_by_session(self, session_id: str) -> List[InterviewMessage]:
        result = await self.db.execute(
            select(InterviewMessage)
            .where(InterviewMessage.session_id == session_id)
            .order_by(InterviewMessage.created_at.asc())
        )
        return list(result.scalars().all())

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: List[dict] = None,
        confidence: str = None
    ) -> InterviewMessage:
        return await self.create(
            session_id=session_id,
            role=role,
            content=content,
            sources_used=sources,
            confidence=confidence
        )
