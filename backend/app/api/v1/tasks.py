from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel
from typing import Optional
from app.schemas.responses import APIResponse
from app.dependencies import get_current_user_id
from app.core.database import get_db
from app.repositories.task_repository import TaskRepository

router = APIRouter(prefix="/tasks", tags=["tasks"])

class CreateTaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    goal_id: Optional[UUID] = None
    key_result_id: Optional[UUID] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    estimated_minutes: Optional[int] = None

class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    scheduled_date: Optional[date] = None

class CompleteTaskRequest(BaseModel):
    outcome_notes: Optional[str] = None
    contribution_to_goal: Optional[str] = None


def _task_to_dict(task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "goal_id": task.goal_id,
        "key_result_id": task.key_result_id,
        "scheduled_date": task.scheduled_date,
        "scheduled_time": str(task.scheduled_time) if task.scheduled_time else None,
        "estimated_minutes": task.estimated_minutes,
        "status": task.status,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "outcome_notes": task.outcome_notes,
        "contribution_to_goal": task.contribution_to_goal,
        "created_at": task.created_at.isoformat() if task.created_at else None
    }


@router.get("")
async def list_tasks(
    scheduled_date: Optional[date] = None,
    goal_id: Optional[UUID] = None,
    status: Optional[str] = None,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = TaskRepository(db)

    if scheduled_date:
        tasks = await repo.get_by_date(str(user_id), scheduled_date)
    elif goal_id:
        tasks = await repo.get_by_goal(str(user_id), str(goal_id))
    elif status:
        tasks = await repo.get_by_status(str(user_id), status)
    else:
        tasks = await repo.get_by_user(str(user_id))

    return APIResponse(data=[_task_to_dict(t) for t in tasks])


@router.post("")
async def create_task(
    request: CreateTaskRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    from datetime import time as time_type
    repo = TaskRepository(db)

    scheduled_time = None
    if request.scheduled_time:
        try:
            parts = request.scheduled_time.split(":")
            scheduled_time = time_type(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
        except:
            pass

    task = await repo.create(
        user_id=str(user_id),
        title=request.title,
        description=request.description,
        goal_id=str(request.goal_id) if request.goal_id else None,
        key_result_id=str(request.key_result_id) if request.key_result_id else None,
        scheduled_date=request.scheduled_date,
        scheduled_time=scheduled_time,
        estimated_minutes=request.estimated_minutes,
        status="pending"
    )

    return APIResponse(data=_task_to_dict(task), message="Task created")


@router.get("/{task_id}")
async def get_task(
    task_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = TaskRepository(db)
    task = await repo.get_by_id(str(task_id))

    if not task or task.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Task not found")

    return APIResponse(data=_task_to_dict(task))


@router.patch("/{task_id}")
async def update_task(
    task_id: UUID,
    request: UpdateTaskRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = TaskRepository(db)
    task = await repo.get_by_id(str(task_id))

    if not task or task.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = request.model_dump(exclude_none=True)
    updated_task = await repo.update(str(task_id), **update_data)

    return APIResponse(data=_task_to_dict(updated_task), message="Task updated")


@router.post("/{task_id}/complete")
async def complete_task(
    task_id: UUID,
    request: CompleteTaskRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = TaskRepository(db)
    task = await repo.mark_complete(
        str(task_id),
        str(user_id),
        outcome_notes=request.outcome_notes
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if request.contribution_to_goal:
        await repo.update(str(task_id), contribution_to_goal=request.contribution_to_goal)
        task = await repo.get_by_id(str(task_id))

    return APIResponse(data=_task_to_dict(task), message="Task completed")


@router.delete("/{task_id}")
async def delete_task(
    task_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = TaskRepository(db)
    task = await repo.get_by_id(str(task_id))

    if not task or task.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Task not found")

    await repo.delete(str(task_id))
    return APIResponse(data=None, message="Task deleted")


@router.get("/stats/completion")
async def get_completion_stats(
    days: int = 30,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = TaskRepository(db)
    stats = await repo.get_completion_stats(str(user_id), days)
    return APIResponse(data=stats)


async def get_tasks_for_date(user_id: str, target_date: date, db: AsyncSession) -> list[dict]:
    repo = TaskRepository(db)
    tasks = await repo.get_by_date(user_id, target_date)
    return [_task_to_dict(t) for t in tasks]
