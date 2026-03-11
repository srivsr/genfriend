from fastapi import APIRouter
from .v1 import (
    auth_router, identity_router, goals_router, tasks_router,
    chat_router, journal_router, progress_router, preferences_router,
    audio_router, planning_router, experiences_router, skills_router,
    snapshots_router, nudge_router, portfolio_router, interview_router,
    woop_router, if_then_router, admin_router, users_router, payment_router,
    strategic_brain_router
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(identity_router)
api_router.include_router(goals_router)
api_router.include_router(tasks_router)
api_router.include_router(chat_router)
api_router.include_router(journal_router)
api_router.include_router(progress_router)
api_router.include_router(preferences_router)
api_router.include_router(audio_router)
api_router.include_router(planning_router)
api_router.include_router(experiences_router)
api_router.include_router(skills_router)
api_router.include_router(snapshots_router)
api_router.include_router(nudge_router)
api_router.include_router(portfolio_router)
api_router.include_router(interview_router)
api_router.include_router(woop_router)
api_router.include_router(if_then_router)
api_router.include_router(admin_router)
api_router.include_router(users_router)
api_router.include_router(payment_router)
api_router.include_router(strategic_brain_router)
