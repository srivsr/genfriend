from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel
from typing import Optional, List
from app.schemas.responses import APIResponse
from app.dependencies import get_current_user_id
from app.core.database import get_db
from app.services.portfolio_service import PortfolioService, InterviewTwinService

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class UpdatePortfolioRequest(BaseModel):
    display_name: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    theme: Optional[str] = None
    social_links: Optional[dict] = None


class PublishPortfolioRequest(BaseModel):
    slug: str
    interview_intro: Optional[str] = None
    interview_topics: Optional[List[str]] = None


class StartInterviewRequest(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None


class AskQuestionRequest(BaseModel):
    question: str


class EndInterviewRequest(BaseModel):
    rating: Optional[str] = None
    feedback: Optional[str] = None


@router.get("")
async def get_portfolio(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = PortfolioService(db)
    portfolio = await service.get_or_create_portfolio(str(user_id))
    return APIResponse(data=portfolio)


@router.patch("")
async def update_portfolio(
    request: UpdatePortfolioRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = PortfolioService(db)
    portfolio = await service.update_portfolio(
        str(user_id),
        display_name=request.display_name,
        headline=request.headline,
        bio=request.bio,
        theme=request.theme,
        social_links=request.social_links
    )
    return APIResponse(data=portfolio, message="Portfolio updated")


@router.post("/publish")
async def publish_portfolio(
    request: PublishPortfolioRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = PortfolioService(db)
    result = await service.publish_portfolio(
        str(user_id),
        request.slug,
        request.interview_intro,
        request.interview_topics
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return APIResponse(data=result, message="Portfolio published!")


@router.get("/public/{slug}")
async def get_public_portfolio(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    service = PortfolioService(db)
    portfolio = await service.get_public_portfolio(slug)

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    return APIResponse(data=portfolio)


interview_router = APIRouter(prefix="/interview", tags=["interview"])


@interview_router.post("/{portfolio_slug}/start")
async def start_interview(
    portfolio_slug: str,
    request: StartInterviewRequest,
    db: AsyncSession = Depends(get_db)
):
    service = InterviewTwinService(db)
    result = await service.start_interview(
        portfolio_slug,
        interviewer_name=request.name,
        interviewer_company=request.company,
        interviewer_email=request.email
    )

    if not result:
        raise HTTPException(status_code=404, detail="Portfolio not found or interviews not enabled")

    return APIResponse(data=result, message="Interview started")


@interview_router.post("/session/{session_id}/ask")
async def ask_question(
    session_id: str,
    request: AskQuestionRequest,
    db: AsyncSession = Depends(get_db)
):
    service = InterviewTwinService(db)
    result = await service.ask_question(session_id, request.question)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return APIResponse(data=result)


@interview_router.post("/session/{session_id}/end")
async def end_interview(
    session_id: str,
    request: EndInterviewRequest,
    db: AsyncSession = Depends(get_db)
):
    service = InterviewTwinService(db)
    result = await service.end_interview(
        session_id,
        rating=request.rating,
        feedback=request.feedback
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return APIResponse(data=result, message="Interview completed")


@interview_router.get("/session/{session_id}/history")
async def get_interview_history(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    service = InterviewTwinService(db)
    history = await service.get_session_history(session_id)
    return APIResponse(data=history)


@router.get("/interviews")
async def get_my_interviews(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    portfolio_service = PortfolioService(db)
    interview_service = InterviewTwinService(db)

    portfolio = await portfolio_service.portfolio_repo.get_by_user(str(user_id))
    if not portfolio:
        return APIResponse(data=[])

    sessions = await interview_service.session_repo.get_by_portfolio(portfolio.id)
    return APIResponse(data=[
        {
            "id": s.id,
            "interviewer_name": s.interviewer_name,
            "interviewer_company": s.interviewer_company,
            "topics": s.topics_discussed,
            "questions_count": len(s.questions_asked or []),
            "rating": s.rating,
            "is_completed": s.is_completed,
            "started_at": s.started_at.isoformat() if s.started_at else None
        }
        for s in sessions
    ])
