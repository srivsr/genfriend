from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.schemas.responses import APIResponse
from app.dependencies import get_current_user_id
from app.core.database import get_db
from app.services.woop_wizard import WOOPWizard, IF_THEN_LIBRARY
from app.services.locke_latham import LockeLathameValidator, format_validation_result
from app.llm.router import LLMRouter

router = APIRouter(prefix="/woop", tags=["woop"])


class WOOPStartResponse(BaseModel):
    message: str
    step: str
    actions: List[str]
    state: Dict[str, Any]


class WOOPProcessRequest(BaseModel):
    state: Dict[str, Any]
    user_input: str


class WOOPProcessResponse(BaseModel):
    message: str
    step: str
    state: Dict[str, Any]
    actions: Optional[List[str]] = None
    options: Optional[List[Dict]] = None
    suggested_if_then: Optional[Dict] = None
    alternatives: Optional[List[Dict]] = None
    validation: Optional[Dict] = None
    execution_system: Optional[Dict] = None
    goal_id: Optional[str] = None
    retry: Optional[bool] = None


class ValidateGoalRequest(BaseModel):
    goal_wish: str
    goal_outcome: Optional[str] = None
    goal_obstacle: Optional[str] = None
    if_then_when: Optional[str] = None
    if_then_then: Optional[str] = None
    future_you: Optional[str] = None
    timeframe: str = "3_months"


@router.post("/start", response_model=APIResponse)
async def start_woop_wizard(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Start the WOOP goal creation wizard."""
    llm = LLMRouter()
    wizard = WOOPWizard(db, llm)
    result = await wizard.start_wizard(user_id)
    return APIResponse(success=True, data=result, message="WOOP wizard started")


@router.post("/process", response_model=APIResponse)
async def process_woop_input(
    request: WOOPProcessRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Process user input in the WOOP wizard flow."""
    if request.state.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Invalid state")
    llm = LLMRouter()
    wizard = WOOPWizard(db, llm)
    result = await wizard.process_input(request.state, request.user_input)
    return APIResponse(success=True, data=result, message=f"Step: {result.get('step')}")


@router.post("/validate", response_model=APIResponse)
async def validate_goal(
    request: ValidateGoalRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Validate a goal against Locke-Latham principles."""
    llm = LLMRouter()
    validator = LockeLathameValidator(llm)
    if_then = None
    if request.if_then_when and request.if_then_then:
        if_then = {"when": request.if_then_when, "then": request.if_then_then}
    validation = await validator.validate(
        goal_wish=request.goal_wish,
        goal_outcome=request.goal_outcome,
        goal_obstacle=request.goal_obstacle,
        if_then_plan=if_then,
        future_you=request.future_you,
        timeframe=request.timeframe
    )
    from app.models.user import User
    user = await db.get(User, user_id)
    preferred_name = user.preferred_name or user.name or "friend"
    formatted = format_validation_result(validation, preferred_name)
    return APIResponse(
        success=True,
        data={
            "validation": {
                "clarity": {"score": validation.clarity.score, "feedback": validation.clarity.feedback},
                "challenge": {"score": validation.challenge.score, "feedback": validation.challenge.feedback},
                "commitment": {"score": validation.commitment.score, "feedback": validation.commitment.feedback},
                "feedback": {"score": validation.feedback.score, "feedback": validation.feedback.feedback},
                "complexity": {"score": validation.complexity.score, "feedback": validation.complexity.feedback},
                "total_score": validation.total_score,
                "percentage": validation.percentage,
                "overall_status": validation.overall_status,
                "strengths": validation.strengths,
                "priority_improvement": validation.priority_improvement
            },
            "formatted_message": formatted
        },
        message=f"Goal score: {validation.total_score}/25"
    )


@router.get("/obstacles", response_model=APIResponse)
async def get_obstacle_library():
    """Get the If-Then plan library for all obstacle types."""
    obstacles = []
    for key, data in IF_THEN_LIBRARY.items():
        obstacles.append({
            "id": key,
            "label": key.replace("_", " ").title(),
            "primary_if_then": {
                "when": data["when"],
                "then": data["then"]
            },
            "alternatives": data.get("alternatives", [])
        })
    return APIResponse(success=True, data=obstacles, message="Obstacle library retrieved")


@router.get("/obstacles/{obstacle_type}", response_model=APIResponse)
async def get_obstacle_if_thens(obstacle_type: str):
    """Get If-Then plans for a specific obstacle type."""
    data = IF_THEN_LIBRARY.get(obstacle_type)
    if not data:
        raise HTTPException(status_code=404, detail="Obstacle type not found")
    return APIResponse(
        success=True,
        data={
            "obstacle_type": obstacle_type,
            "primary": {"when": data["when"], "then": data["then"]},
            "alternatives": data.get("alternatives", [])
        },
        message=f"If-Then plans for {obstacle_type}"
    )
