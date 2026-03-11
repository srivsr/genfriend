from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.schemas.responses import APIResponse
from app.dependencies import get_current_user_id
from app.core.database import get_db
from app.models.if_then_plan import IfThenPlan, IfThenLog
from app.models.goal import Goal

router = APIRouter(prefix="/if-then", tags=["if-then-plans"])


def _plan_to_dict(plan: IfThenPlan) -> dict:
    return {
        "id": plan.id,
        "goal_id": plan.goal_id,
        "when_trigger": plan.when_trigger,
        "then_action": plan.then_action,
        "obstacle_type": plan.obstacle_type,
        "is_primary": plan.is_primary,
        "is_active": plan.is_active,
        "times_triggered": plan.times_triggered,
        "times_used": plan.times_used,
        "times_effective": plan.times_effective,
        "effectiveness_rate": plan.effectiveness_rate,
        "created_at": plan.created_at.isoformat() if plan.created_at else None
    }


class CreateIfThenRequest(BaseModel):
    when_trigger: str
    then_action: str
    obstacle_type: Optional[str] = None
    is_primary: bool = False


class UpdateIfThenRequest(BaseModel):
    when_trigger: Optional[str] = None
    then_action: Optional[str] = None
    is_active: Optional[bool] = None


class LogIfThenUseRequest(BaseModel):
    task_id: Optional[str] = None
    was_triggered: bool = True
    was_used: bool = False
    was_effective: bool = False
    context: Optional[str] = None
    notes: Optional[str] = None


@router.get("/goals/{goal_id}/plans", response_model=APIResponse)
async def get_goal_if_then_plans(
    goal_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Get all If-Then plans for a goal."""
    goal = await db.get(Goal, goal_id)
    if not goal or goal.user_id != user_id:
        raise HTTPException(status_code=404, detail="Goal not found")
    result = await db.execute(
        select(IfThenPlan)
        .where(IfThenPlan.goal_id == goal_id)
        .order_by(IfThenPlan.is_primary.desc(), IfThenPlan.created_at.desc())
    )
    plans = result.scalars().all()
    return APIResponse(
        success=True,
        data=[_plan_to_dict(p) for p in plans],
        message=f"Found {len(plans)} If-Then plans"
    )


@router.post("/goals/{goal_id}/plans", response_model=APIResponse)
async def create_if_then_plan(
    goal_id: str,
    request: CreateIfThenRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Create a new If-Then plan for a goal."""
    goal = await db.get(Goal, goal_id)
    if not goal or goal.user_id != user_id:
        raise HTTPException(status_code=404, detail="Goal not found")
    if request.is_primary:
        await db.execute(
            update(IfThenPlan)
            .where(IfThenPlan.goal_id == goal_id)
            .values(is_primary=False)
        )
    plan = IfThenPlan(
        goal_id=goal_id,
        when_trigger=request.when_trigger,
        then_action=request.then_action,
        obstacle_type=request.obstacle_type or goal.woop_primary_obstacle,
        is_primary=request.is_primary
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return APIResponse(success=True, data=_plan_to_dict(plan), message="If-Then plan created")


@router.patch("/plans/{plan_id}", response_model=APIResponse)
async def update_if_then_plan(
    plan_id: str,
    request: UpdateIfThenRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Update an If-Then plan."""
    plan = await db.get(IfThenPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    goal = await db.get(Goal, plan.goal_id)
    if not goal or goal.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if request.when_trigger is not None:
        plan.when_trigger = request.when_trigger
    if request.then_action is not None:
        plan.then_action = request.then_action
    if request.is_active is not None:
        plan.is_active = request.is_active
    await db.commit()
    await db.refresh(plan)
    return APIResponse(success=True, data=_plan_to_dict(plan), message="If-Then plan updated")


@router.delete("/plans/{plan_id}", response_model=APIResponse)
async def delete_if_then_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Delete an If-Then plan."""
    plan = await db.get(IfThenPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    goal = await db.get(Goal, plan.goal_id)
    if not goal or goal.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    await db.delete(plan)
    await db.commit()
    return APIResponse(success=True, data=None, message="If-Then plan deleted")


@router.post("/plans/{plan_id}/log", response_model=APIResponse)
async def log_if_then_use(
    plan_id: str,
    request: LogIfThenUseRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Log the use of an If-Then plan (for effectiveness tracking)."""
    plan = await db.get(IfThenPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    goal = await db.get(Goal, plan.goal_id)
    if not goal or goal.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    log = IfThenLog(
        if_then_plan_id=plan_id,
        task_id=request.task_id,
        was_triggered=request.was_triggered,
        was_used=request.was_used,
        was_effective=request.was_effective,
        context=request.context,
        notes=request.notes
    )
    db.add(log)

    if request.was_triggered:
        plan.times_triggered += 1
    if request.was_used:
        plan.times_used += 1
    if request.was_effective:
        plan.times_effective += 1

    await db.commit()
    await db.refresh(plan)

    return APIResponse(
        success=True,
        data={
            "plan": _plan_to_dict(plan),
            "log_id": log.id,
            "message": "If-Then plan use logged"
        },
        message=f"Effectiveness rate: {plan.effectiveness_rate:.1f}%"
    )


@router.get("/plans/{plan_id}/effectiveness", response_model=APIResponse)
async def get_plan_effectiveness(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Get effectiveness statistics for an If-Then plan."""
    plan = await db.get(IfThenPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    goal = await db.get(Goal, plan.goal_id)
    if not goal or goal.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(
        select(IfThenLog)
        .where(IfThenLog.if_then_plan_id == plan_id)
        .order_by(IfThenLog.created_at.desc())
        .limit(20)
    )
    logs = result.scalars().all()

    return APIResponse(
        success=True,
        data={
            "plan": _plan_to_dict(plan),
            "stats": {
                "total_triggers": plan.times_triggered,
                "times_used": plan.times_used,
                "times_effective": plan.times_effective,
                "effectiveness_rate": plan.effectiveness_rate,
                "usage_rate": (plan.times_used / plan.times_triggered * 100) if plan.times_triggered > 0 else 0
            },
            "recent_logs": [
                {
                    "id": log.id,
                    "was_triggered": log.was_triggered,
                    "was_used": log.was_used,
                    "was_effective": log.was_effective,
                    "context": log.context,
                    "notes": log.notes,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ]
        },
        message=f"Effectiveness: {plan.effectiveness_rate:.1f}%"
    )


@router.get("/user/summary", response_model=APIResponse)
async def get_user_if_then_summary(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Get If-Then plan summary across all user's goals."""
    result = await db.execute(
        select(Goal.id).where(Goal.user_id == user_id, Goal.status == "active")
    )
    goal_ids = [row[0] for row in result.fetchall()]
    if not goal_ids:
        return APIResponse(success=True, data={"plans": [], "summary": {}}, message="No active goals")
    plans_result = await db.execute(
        select(IfThenPlan)
        .where(IfThenPlan.goal_id.in_(goal_ids), IfThenPlan.is_active == True)
    )
    plans = plans_result.scalars().all()
    total_triggers = sum(p.times_triggered for p in plans)
    total_effective = sum(p.times_effective for p in plans)
    overall_effectiveness = (total_effective / total_triggers * 100) if total_triggers > 0 else 0
    plans_by_obstacle = {}
    for plan in plans:
        obstacle = plan.obstacle_type or "unknown"
        if obstacle not in plans_by_obstacle:
            plans_by_obstacle[obstacle] = []
        plans_by_obstacle[obstacle].append(_plan_to_dict(plan))

    return APIResponse(
        success=True,
        data={
            "plans": [_plan_to_dict(p) for p in plans],
            "by_obstacle": plans_by_obstacle,
            "summary": {
                "total_plans": len(plans),
                "total_triggers": total_triggers,
                "total_effective": total_effective,
                "overall_effectiveness": overall_effectiveness,
                "most_effective_plan": max(plans, key=lambda p: p.effectiveness_rate).id if plans else None
            }
        },
        message=f"Overall effectiveness: {overall_effectiveness:.1f}%"
    )
