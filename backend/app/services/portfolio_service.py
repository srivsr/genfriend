from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.portfolio_repository import PortfolioRepository, InterviewSessionRepository, InterviewMessageRepository
from app.repositories.experience_repository import ExperienceRepository, SkillProgressRepository
from app.services.embedding_service import EmbeddingService
from app.llm import LLMRouter, TaskType


@dataclass
class InterviewContext:
    portfolio_id: str
    user_name: str
    headline: str
    bio: str
    top_skills: List[dict]
    key_experiences: List[dict]
    interview_topics: List[str]


class PortfolioService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.portfolio_repo = PortfolioRepository(db)
        self.exp_repo = ExperienceRepository(db)
        self.skill_repo = SkillProgressRepository(db)

    async def get_or_create_portfolio(self, user_id: str) -> Dict:
        portfolio = await self.portfolio_repo.get_or_create(user_id)
        return await self._enrich_portfolio(user_id, portfolio)

    async def _enrich_portfolio(self, user_id: str, portfolio) -> Dict:
        experiences = await self.exp_repo.get_public(user_id)
        top_skills = await self.skill_repo.get_top_skills(user_id, 10)
        exp_stats = await self.exp_repo.get_stats(user_id)

        return {
            "id": portfolio.id,
            "display_name": portfolio.display_name,
            "headline": portfolio.headline,
            "bio": portfolio.bio,
            "avatar_url": portfolio.avatar_url,
            "is_public": portfolio.is_public,
            "public_slug": portfolio.public_slug,
            "theme": portfolio.theme,
            "interview_enabled": portfolio.interview_enabled,
            "featured_experiences": portfolio.featured_experiences or [],
            "featured_skills": portfolio.featured_skills or [],
            "experiences": [self._exp_to_dict(e) for e in experiences],
            "skills": [self._skill_to_dict(s) for s in top_skills],
            "stats": exp_stats,
            "social_links": portfolio.social_links or {},
            "last_updated": portfolio.last_updated.isoformat() if portfolio.last_updated else None
        }

    async def update_portfolio(
        self,
        user_id: str,
        display_name: str = None,
        headline: str = None,
        bio: str = None,
        theme: str = None,
        social_links: dict = None
    ) -> Dict:
        portfolio = await self.portfolio_repo.get_by_user(user_id)
        if not portfolio:
            portfolio = await self.portfolio_repo.get_or_create(user_id)

        update_data = {}
        if display_name:
            update_data["display_name"] = display_name
        if headline:
            update_data["headline"] = headline
        if bio:
            update_data["bio"] = bio
        if theme:
            update_data["theme"] = theme
        if social_links:
            update_data["social_links"] = social_links

        if update_data:
            await self.portfolio_repo.update(portfolio.id, **update_data)

        portfolio = await self.portfolio_repo.get_by_id(portfolio.id)
        return await self._enrich_portfolio(user_id, portfolio)

    async def publish_portfolio(
        self,
        user_id: str,
        slug: str,
        interview_intro: str = None,
        interview_topics: List[str] = None
    ) -> Dict:
        portfolio = await self.portfolio_repo.get_by_user(user_id)
        if not portfolio:
            return {"error": "Portfolio not found"}

        existing = await self.portfolio_repo.get_by_slug(slug)
        if existing and existing.id != portfolio.id:
            return {"error": "Slug already taken"}

        await self.portfolio_repo.update_public_settings(portfolio.id, True, slug)

        if interview_intro or interview_topics:
            await self.portfolio_repo.enable_interview(
                portfolio.id, interview_intro, interview_topics
            )

        portfolio = await self.portfolio_repo.get_by_id(portfolio.id)
        return {
            "published": True,
            "public_url": f"/p/{slug}",
            "interview_enabled": portfolio.interview_enabled
        }

    async def get_public_portfolio(self, slug: str) -> Optional[Dict]:
        portfolio = await self.portfolio_repo.get_by_slug(slug)
        if not portfolio:
            return None

        return await self._enrich_portfolio(portfolio.user_id, portfolio)

    def _exp_to_dict(self, exp) -> Dict:
        return {
            "id": exp.id,
            "title": exp.title,
            "description": exp.description,
            "type": exp.experience_type,
            "skills": exp.skills_demonstrated or [],
            "outcome": exp.outcome,
            "is_verified": exp.is_verified
        }

    def _skill_to_dict(self, skill) -> Dict:
        level_names = {1: "Novice", 2: "Beginner", 3: "Intermediate", 4: "Advanced", 5: "Expert", 6: "Master"}
        return {
            "name": skill.skill_name,
            "category": skill.skill_category,
            "level": skill.current_level,
            "level_name": level_names.get(skill.current_level, "Novice"),
            "mastery": skill.mastery_percentage,
            "evidence_count": skill.evidence_count
        }


class InterviewTwinService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.portfolio_repo = PortfolioRepository(db)
        self.session_repo = InterviewSessionRepository(db)
        self.message_repo = InterviewMessageRepository(db)
        self.exp_repo = ExperienceRepository(db)
        self.skill_repo = SkillProgressRepository(db)
        self.embedding_service = EmbeddingService(db)
        self.llm = LLMRouter()

    async def start_interview(
        self,
        portfolio_slug: str,
        interviewer_name: str = None,
        interviewer_company: str = None,
        interviewer_email: str = None
    ) -> Optional[Dict]:
        portfolio = await self.portfolio_repo.get_by_slug(portfolio_slug)
        if not portfolio or not portfolio.interview_enabled:
            return None

        session = await self.session_repo.start_session(
            portfolio_id=portfolio.id,
            interviewer_name=interviewer_name,
            interviewer_company=interviewer_company,
            interviewer_email=interviewer_email
        )

        intro_message = await self._generate_intro(portfolio)
        await self.message_repo.add_message(
            session_id=session.id,
            role="assistant",
            content=intro_message
        )

        return {
            "session_id": session.id,
            "message": intro_message,
            "topics": portfolio.interview_topics or ["Experience", "Skills", "Projects", "Goals"]
        }

    async def ask_question(
        self,
        session_id: str,
        question: str
    ) -> Dict:
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            return {"error": "Session not found"}

        await self.message_repo.add_message(
            session_id=session_id,
            role="user",
            content=question
        )

        portfolio = await self.portfolio_repo.get_by_id(session.portfolio_id)
        context = await self._build_interview_context(portfolio)
        relevant_data = await self._retrieve_relevant_info(portfolio.user_id, question)
        response = await self._generate_response(question, context, relevant_data)

        topic = self._classify_topic(question)
        await self.session_repo.update_topics(session_id, question, topic)

        await self.message_repo.add_message(
            session_id=session_id,
            role="assistant",
            content=response["answer"],
            sources=response.get("sources"),
            confidence=response.get("confidence")
        )

        return {
            "answer": response["answer"],
            "sources": response.get("sources"),
            "confidence": response.get("confidence"),
            "follow_up_suggestions": response.get("follow_ups", [])
        }

    async def end_interview(
        self,
        session_id: str,
        rating: str = None,
        feedback: str = None
    ) -> Dict:
        session = await self.session_repo.end_session(session_id, rating, feedback)
        if not session:
            return {"error": "Session not found"}

        messages = await self.message_repo.get_by_session(session_id)
        return {
            "session_id": session_id,
            "duration_minutes": self._calculate_duration(session),
            "questions_asked": len(session.questions_asked or []),
            "topics_covered": session.topics_discussed or [],
            "message_count": len(messages)
        }

    async def get_session_history(self, session_id: str) -> List[Dict]:
        messages = await self.message_repo.get_by_session(session_id)
        return [
            {
                "role": m.role,
                "content": m.content,
                "sources": m.sources_used,
                "timestamp": m.created_at.isoformat() if m.created_at else None
            }
            for m in messages
        ]

    async def _generate_intro(self, portfolio) -> str:
        name = portfolio.display_name or "this professional"
        headline = portfolio.headline or "a skilled professional"
        intro = portfolio.interview_intro or f"Hi! I'm the digital twin of {name}. {headline}. Feel free to ask me about my experience, skills, projects, or anything else you'd like to know!"
        return intro

    async def _build_interview_context(self, portfolio) -> InterviewContext:
        experiences = await self.exp_repo.get_public(portfolio.user_id)
        skills = await self.skill_repo.get_top_skills(portfolio.user_id, 10)

        return InterviewContext(
            portfolio_id=portfolio.id,
            user_name=portfolio.display_name or "User",
            headline=portfolio.headline or "",
            bio=portfolio.bio or "",
            top_skills=[
                {"name": s.skill_name, "level": s.current_level, "mastery": s.mastery_percentage}
                for s in skills
            ],
            key_experiences=[
                {"title": e.title, "description": e.description, "skills": e.skills_demonstrated, "verified": e.is_verified}
                for e in experiences[:10]
            ],
            interview_topics=portfolio.interview_topics or []
        )

    async def _retrieve_relevant_info(self, user_id: str, question: str) -> List[Dict]:
        results = await self.embedding_service.search(
            user_id=user_id,
            query=question,
            source_types=["experience", "goal", "journal"],
            top_k=5
        )
        return [r for r in results if r.get("similarity", 0) > 0.3]

    async def _generate_response(
        self,
        question: str,
        context: InterviewContext,
        relevant_data: List[Dict]
    ) -> Dict:
        relevant_context = "\n".join([
            f"- [{r['source_type']}] {r['content']}"
            for r in relevant_data[:5]
        ])

        prompt = f"""You are the digital twin of {context.user_name}, a professional with this background:
{context.headline}
{context.bio}

Top Skills: {[s['name'] for s in context.top_skills]}

Key Experiences:
{chr(10).join([f"- {e['title']}: {e['description'][:100]}" for e in context.key_experiences[:5]])}

Relevant Information from Portfolio:
{relevant_context}

Question from Interviewer: {question}

Respond as if you ARE this person. Be professional, confident, and specific.
Reference actual experiences and skills when relevant.
If you don't have specific information, say so honestly.
Keep responses focused and under 200 words unless more detail is needed.

After your response, suggest 2 follow-up questions they might want to ask."""

        response = await self.llm.route(prompt=prompt, task_type=TaskType.GENERATION)

        lines = response.content.strip().split("\n")
        main_answer = []
        follow_ups = []
        in_followups = False

        for line in lines:
            if "follow-up" in line.lower() or "you might ask" in line.lower():
                in_followups = True
            elif in_followups and line.strip():
                follow_ups.append(line.strip().lstrip("- ").lstrip("1.").lstrip("2.").strip())
            else:
                main_answer.append(line)

        return {
            "answer": "\n".join(main_answer).strip(),
            "sources": [{"type": r["source_type"], "id": r["source_id"]} for r in relevant_data],
            "confidence": "high" if relevant_data else "moderate",
            "follow_ups": follow_ups[:2]
        }

    def _classify_topic(self, question: str) -> str:
        lower = question.lower()
        if any(w in lower for w in ["experience", "project", "worked", "built", "created"]):
            return "experience"
        elif any(w in lower for w in ["skill", "technology", "tool", "framework"]):
            return "skills"
        elif any(w in lower for w in ["goal", "future", "plan", "want"]):
            return "goals"
        elif any(w in lower for w in ["strength", "weakness", "challenge"]):
            return "self-reflection"
        elif any(w in lower for w in ["team", "lead", "manage", "collaborate"]):
            return "leadership"
        return "general"

    def _calculate_duration(self, session) -> int:
        if session.ended_at and session.started_at:
            delta = session.ended_at - session.started_at
            return int(delta.total_seconds() / 60)
        return 0
