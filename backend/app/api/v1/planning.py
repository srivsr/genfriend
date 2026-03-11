from fastapi import APIRouter, Depends
from uuid import UUID
from datetime import date
from app.schemas.requests import CreateTaskRequest, UpdateTaskRequest, CreateGoalRequest, UpdateGoalRequest
from app.schemas.responses import APIResponse, TaskResponse, GoalResponse, DailyPlanResponse
from app.agents import PlannerAgent, AgentContext
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/planning", tags=["planning"])
planner = PlannerAgent()

@router.get("/today", response_model=APIResponse[DailyPlanResponse])
async def get_today(user_id: UUID = Depends(get_current_user_id)):
    plan = await planner.create_daily_plan(str(user_id))
    return APIResponse(data=DailyPlanResponse(date=date.today(), tasks=[], summary=plan.summary))

@router.post("/today", response_model=APIResponse[DailyPlanResponse])
async def generate_today(user_id: UUID = Depends(get_current_user_id)):
    plan = await planner.create_daily_plan(str(user_id))
    tasks = [TaskResponse(
        id=UUID("00000000-0000-0000-0000-000000000000"),
        title=t.title,
        description=None,
        goal_id=None,
        priority=t.priority,
        status="pending",
        scheduled_date=date.today(),
        scheduled_time_block=t.time_block,
        completed_at=None,
        created_at=date.today()
    ) for t in plan.tasks]
    return APIResponse(data=DailyPlanResponse(date=date.today(), tasks=tasks, summary=plan.summary))

@router.get("/tasks", response_model=APIResponse[list[TaskResponse]])
async def list_tasks(user_id: UUID = Depends(get_current_user_id)):
    return APIResponse(data=[])

@router.post("/tasks", response_model=APIResponse[TaskResponse])
async def create_task(request: CreateTaskRequest, user_id: UUID = Depends(get_current_user_id)):
    return APIResponse(data=TaskResponse(
        id=UUID("00000000-0000-0000-0000-000000000000"),
        title=request.title,
        description=request.description,
        goal_id=request.goal_id,
        priority=request.priority,
        status="pending",
        scheduled_date=request.scheduled_date,
        scheduled_time_block=request.scheduled_time_block,
        completed_at=None,
        created_at=date.today()
    ), message="Task created")

@router.get("/goals", response_model=APIResponse[list[GoalResponse]])
async def list_goals(user_id: UUID = Depends(get_current_user_id)):
    return APIResponse(data=[])

@router.post("/goals", response_model=APIResponse[GoalResponse])
async def create_goal(request: CreateGoalRequest, user_id: UUID = Depends(get_current_user_id)):
    return APIResponse(data=GoalResponse(
        id=UUID("00000000-0000-0000-0000-000000000000"),
        title=request.title,
        description=request.description,
        category=request.category,
        status="active",
        target_date=request.target_date,
        created_at=date.today()
    ), message="Goal created")
