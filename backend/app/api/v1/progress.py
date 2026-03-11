from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import date, timedelta
from typing import Optional
from pydantic import BaseModel

from app.schemas.responses import APIResponse
from app.mentor import pattern_detector, goal_coach, journal_keeper
from app.dependencies import get_current_user_id
from app.core import get_db
from app.models.goal import Goal
from app.models.leading_indicator import DailyLeadingIndicator, ProgressVelocity

router = APIRouter(prefix="/progress", tags=["progress"])


class LeadingIndicatorInput(BaseModel):
    showed_up: bool = True
    task_attempted: bool = False
    if_then_triggered: bool = False
    if_then_used: bool = False
    time_invested_minutes: int = 0
    engagement_quality: Optional[int] = None  # 1-5


@router.get("/overview")
async def get_overview(user_id: UUID = Depends(get_current_user_id)):
    goals = await goal_coach.get_active_goals(str(user_id))
    wins = await journal_keeper.get_recent_wins(str(user_id))

    total_goals = len(goals)
    on_track = len([g for g in goals if g.get("progress_percent", 0) >= 50])

    return APIResponse(data={
        "total_goals": total_goals,
        "goals_on_track": on_track,
        "goals_at_risk": total_goals - on_track,
        "wins_this_week": len(wins),
        "streak_days": 0
    })


@router.get("/patterns")
async def get_patterns(user_id: UUID = Depends(get_current_user_id)):
    patterns = await pattern_detector.get_recent_patterns(str(user_id))
    return APIResponse(data=patterns)


@router.post("/detect-patterns")
async def detect_patterns(user_id: UUID = Depends(get_current_user_id)):
    patterns = await pattern_detector.detect_patterns(str(user_id))
    return APIResponse(data=[{
        "pattern_type": p.pattern_type.value,
        "description": p.description,
        "confidence": float(p.confidence),
        "suggested_action": p.suggested_action
    } for p in patterns])


@router.get("/journey")
async def get_journey(user_id: UUID = Depends(get_current_user_id)):
    return APIResponse(data={
        "milestones": [],
        "growth_areas": [],
        "timeline": []
    })


@router.get("/goals/{goal_id}/analysis")
async def get_goal_progress_analysis(
    goal_id: str,
    include_forecast: bool = True,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive multi-dimensional progress analysis for a goal."""
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    today = date.today()
    week_ago = today - timedelta(days=7)

    indicators_result = await db.execute(
        select(DailyLeadingIndicator)
        .where(
            DailyLeadingIndicator.goal_id == goal_id,
            DailyLeadingIndicator.date >= week_ago
        )
        .order_by(DailyLeadingIndicator.date.desc())
    )
    indicators = indicators_result.scalars().all()

    weekly_leading_score = (
        sum(i.leading_score or 0 for i in indicators) / len(indicators)
        if indicators else 0
    )
    days_active = len([i for i in indicators if i.showed_up])

    effective_progress = max(
        goal.progress_percent or 0,
        goal.initial_progress_percent or 20
    )

    response_data = {
        "overall_progress": effective_progress,
        "initial_progress": goal.initial_progress_percent or 20,
        "dimensions": {
            "effort": {
                "score": goal.effort_score or 0,
                "trend": "steady",
                "components": {
                    "days_engaged_this_week": days_active,
                    "time_invested": sum(i.time_invested_minutes or 0 for i in indicators),
                    "if_then_triggers": len([i for i in indicators if i.if_then_triggered])
                }
            },
            "consistency": {
                "score": goal.consistency_score or 0,
                "trend": "steady",
                "components": {
                    "current_streak": goal.current_streak or 0,
                    "total_active_days": goal.total_active_days or 0,
                    "weekly_rhythm": (days_active / 7) * 100
                }
            },
            "completion": {
                "score": goal.completion_score or 0,
                "trend": "steady",
                "components": {
                    "tasks_completed": goal.total_tasks_completed or 0,
                    "completion_rate": (
                        (goal.total_tasks_completed / goal.total_tasks_created * 100)
                        if goal.total_tasks_created else 0
                    )
                }
            },
            "momentum": {
                "score": goal.momentum_score or 0,
                "trend": goal.velocity_trend or "steady",
                "components": {
                    "velocity": goal.current_velocity or 1.0
                }
            }
        },
        "streak": {
            "current": goal.current_streak or 0,
            "total_active_days": goal.total_active_days or 0,
            "best": goal.longest_streak or 0,
            "freeze_days_available": goal.freeze_days_available or 0,
            "freeze_days_used": goal.freeze_days_used or 0,
            "recovery_count": goal.streak_recovery_count or 0
        },
        "leading_indicators": {
            "today": next(
                (
                    {
                        "showed_up": i.showed_up,
                        "task_attempted": i.task_attempted,
                        "if_then_used": i.if_then_used,
                        "time_invested": i.time_invested_minutes,
                        "score": i.leading_score
                    }
                    for i in indicators if i.date == today
                ),
                None
            ),
            "weekly_average": weekly_leading_score,
            "hit_rate": (days_active / 7) * 100
        }
    }

    if include_forecast and goal.predicted_completion_date:
        days_diff = (goal.predicted_completion_date - goal.end_date).days
        response_data["velocity"] = {
            "current": goal.current_velocity or 1.0,
            "trend": goal.velocity_trend or "steady",
            "forecast": {
                "predicted_completion": goal.predicted_completion_date.isoformat(),
                "days_ahead_behind": days_diff,
                "status": "ahead" if days_diff < 0 else "behind" if days_diff > 0 else "on_track"
            }
        }
    else:
        response_data["velocity"] = {
            "current": goal.current_velocity or 1.0,
            "trend": goal.velocity_trend or "steady",
            "forecast": None
        }

    return APIResponse(data=response_data)


@router.get("/goals/{goal_id}/leading-indicators")
async def get_leading_indicators(
    goal_id: str,
    period: str = Query("this_week", description="today | this_week | this_month"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get leading indicators history for a goal."""
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    today = date.today()
    if period == "today":
        start_date = today
    elif period == "this_week":
        start_date = today - timedelta(days=7)
    else:  # this_month
        start_date = today - timedelta(days=30)

    indicators_result = await db.execute(
        select(DailyLeadingIndicator)
        .where(
            DailyLeadingIndicator.goal_id == goal_id,
            DailyLeadingIndicator.date >= start_date
        )
        .order_by(DailyLeadingIndicator.date.desc())
    )
    indicators = indicators_result.scalars().all()

    daily_data = [
        {
            "date": i.date.isoformat(),
            "showed_up": i.showed_up,
            "task_attempted": i.task_attempted,
            "if_then_triggered": i.if_then_triggered,
            "if_then_used": i.if_then_used,
            "time_invested": i.time_invested_minutes,
            "engagement_quality": i.engagement_quality,
            "score": i.leading_score
        }
        for i in indicators
    ]

    avg_score = sum(i.leading_score or 0 for i in indicators) / len(indicators) if indicators else 0
    days_showed_up = len([i for i in indicators if i.showed_up])

    return APIResponse(data={
        "period": period,
        "daily": daily_data,
        "summary": {
            "average_score": round(avg_score, 1),
            "days_showed_up": days_showed_up,
            "total_days": len(indicators),
            "hit_rate": round(days_showed_up / len(indicators) * 100, 1) if indicators else 0,
            "strongest": "showing_up" if days_showed_up > len(indicators) * 0.7 else "needs_work",
            "total_time_invested": sum(i.time_invested_minutes or 0 for i in indicators)
        }
    })


@router.post("/goals/{goal_id}/leading-indicators")
async def log_leading_indicators(
    goal_id: str,
    data: LeadingIndicatorInput,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Log today's leading indicators for a goal."""
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    today = date.today()

    existing = await db.execute(
        select(DailyLeadingIndicator).where(
            DailyLeadingIndicator.goal_id == goal_id,
            DailyLeadingIndicator.date == today
        )
    )
    indicator = existing.scalar_one_or_none()

    if indicator:
        indicator.showed_up = data.showed_up
        indicator.task_attempted = data.task_attempted
        indicator.if_then_triggered = data.if_then_triggered
        indicator.if_then_used = data.if_then_used
        indicator.time_invested_minutes = data.time_invested_minutes
        indicator.engagement_quality = data.engagement_quality
    else:
        indicator = DailyLeadingIndicator(
            user_id=user_id,
            goal_id=goal_id,
            date=today,
            showed_up=data.showed_up,
            task_attempted=data.task_attempted,
            if_then_triggered=data.if_then_triggered,
            if_then_used=data.if_then_used,
            time_invested_minutes=data.time_invested_minutes,
            engagement_quality=data.engagement_quality
        )
        db.add(indicator)

    indicator.leading_score = indicator.calculate_leading_score()

    if data.showed_up:
        goal.total_active_days = (goal.total_active_days or 0) + 1

    await db.commit()

    week_ago = today - timedelta(days=7)
    week_indicators = await db.execute(
        select(DailyLeadingIndicator)
        .where(
            DailyLeadingIndicator.goal_id == goal_id,
            DailyLeadingIndicator.date >= week_ago
        )
    )
    week_data = week_indicators.scalars().all()
    weekly_score = sum(i.leading_score or 0 for i in week_data) / len(week_data) if week_data else 0

    insight = "Great job showing up today!" if data.showed_up else "Tomorrow is a fresh start."
    if data.if_then_triggered and data.if_then_used:
        insight = "You used your If-Then plan when the obstacle hit. That's building real habit strength!"
    elif data.time_invested_minutes >= 15:
        insight = f"Solid {data.time_invested_minutes} minutes invested. Consistency beats intensity."

    return APIResponse(data={
        "today_score": indicator.leading_score,
        "weekly_score": round(weekly_score, 1),
        "streak_status": {
            "current": goal.current_streak,
            "total_active_days": goal.total_active_days
        },
        "insight": insight
    }, message="Leading indicators logged successfully")


@router.post("/goals/{goal_id}/streak/use-freeze")
async def use_freeze_day(
    goal_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Use a freeze day to protect streak."""
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    if (goal.freeze_days_available or 0) <= 0:
        raise HTTPException(status_code=400, detail="No freeze days available")

    goal.freeze_days_available -= 1
    goal.freeze_days_used = (goal.freeze_days_used or 0) + 1

    await db.commit()

    return APIResponse(data={
        "streak_protected": True,
        "current_streak": goal.current_streak,
        "freeze_days_remaining": goal.freeze_days_available
    }, message="Freeze day used. Streak protected!")


@router.get("/goals/{goal_id}/streak/history")
async def get_streak_history(
    goal_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get streak history and resilience metrics."""
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    total_possible_days = (date.today() - goal.start_date).days if goal.start_date else 0
    resilience_score = (
        (goal.total_active_days or 0) / total_possible_days * 100
        if total_possible_days > 0 else 0
    )

    return APIResponse(data={
        "current_streak": goal.current_streak or 0,
        "total_active_days": goal.total_active_days or 0,
        "best_streak": goal.longest_streak or 0,
        "freeze_days": {
            "available": goal.freeze_days_available or 0,
            "used": goal.freeze_days_used or 0,
            "earned": (goal.freeze_days_available or 0) + (goal.freeze_days_used or 0)
        },
        "recovery_count": goal.streak_recovery_count or 0,
        "last_recovery_date": goal.last_recovery_date.isoformat() if goal.last_recovery_date else None,
        "resilience_score": round(resilience_score, 1),
        "total_possible_days": total_possible_days
    })
