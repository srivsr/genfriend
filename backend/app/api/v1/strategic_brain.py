from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.schemas.responses import APIResponse
from app.dependencies import get_current_user_id
from app.core.database import get_db
from app.repositories.strategic_brain_repository import (
    OpportunityScoreRepository, DecisionLogRepository,
    ExperimentRepository, DistractionRuleRepository
)
from app.repositories.goal_repository import GoalRepository
from app.models.identity import Identity
from sqlalchemy import select, update

router = APIRouter(prefix="/strategic-brain", tags=["strategic-brain"])


class ScoreOpportunityRequest(BaseModel):
    description: str
    goal_id: Optional[str] = None

class LogDecisionRequest(BaseModel):
    decision: str
    why: Optional[str] = None
    expected_outcome: Optional[str] = None
    review_days: int = 14
    tags: Optional[list[str]] = None
    goal_id: Optional[str] = None

class UpdateDecisionRequest(BaseModel):
    actual_outcome: Optional[str] = None
    status: Optional[str] = None

class ReviewDecisionRequest(BaseModel):
    actual_outcome: str

class OpenExperimentRequest(BaseModel):
    hypothesis: str
    action: Optional[str] = None
    tags: Optional[list[str]] = None

class CloseExperimentRequest(BaseModel):
    result: str
    learning: Optional[str] = None

class CreateRuleRequest(BaseModel):
    rule_name: str
    condition: str
    action: str
    rule_type: str = "custom"

class UpdateRuleRequest(BaseModel):
    is_active: Optional[bool] = None
    rule_name: Optional[str] = None
    condition: Optional[str] = None
    action: Optional[str] = None

class UpdateStatusRequest(BaseModel):
    status: str

class UpdateConstraintsRequest(BaseModel):
    weekly_hours_available: Optional[int] = None
    monthly_budget: Optional[float] = None
    health_limits: Optional[str] = None
    risk_tolerance: Optional[str] = None

class AntiGoalsRequest(BaseModel):
    anti_goals: list[str]

class CheckConflictRequest(BaseModel):
    proposal: str


# --- Opportunities ---

@router.post("/opportunities/score")
async def score_opportunity(
    request: ScoreOpportunityRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    from app.agents.strategic_brain import StrategicBrainAgent
    agent = StrategicBrainAgent()
    result = await agent.score_opportunity(str(user_id), request.description)
    return APIResponse(data=result.data, message=result.content)

@router.get("/opportunities")
async def list_opportunities(
    status: Optional[str] = None,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = OpportunityScoreRepository(db)
    if status:
        items = await repo.get_by_status(str(user_id), status)
    else:
        items = await repo.get_by_user(str(user_id))
    return APIResponse(data=[{
        "id": o.id, "title": o.title, "total_score": o.total_score,
        "status": o.status, "created_at": str(o.created_at),
        "revenue_potential": o.revenue_potential, "strategic_fit": o.strategic_fit,
        "effort_complexity": o.effort_complexity, "skill_match": o.skill_match,
        "time_to_first_win": o.time_to_first_win, "risk_regret_cost": o.risk_regret_cost,
        "reasoning": o.reasoning, "anti_goal_conflicts": o.anti_goal_conflicts
    } for o in items])

@router.get("/opportunities/{opportunity_id}")
async def get_opportunity(
    opportunity_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = OpportunityScoreRepository(db)
    opp = await repo.get_by_id(opportunity_id)
    if not opp or opp.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return APIResponse(data={
        "id": opp.id, "title": opp.title, "description": opp.description,
        "total_score": opp.total_score, "status": opp.status,
        "revenue_potential": opp.revenue_potential, "strategic_fit": opp.strategic_fit,
        "effort_complexity": opp.effort_complexity, "skill_match": opp.skill_match,
        "time_to_first_win": opp.time_to_first_win, "risk_regret_cost": opp.risk_regret_cost,
        "reasoning": opp.reasoning, "anti_goal_conflicts": opp.anti_goal_conflicts,
        "created_at": str(opp.created_at)
    })

@router.patch("/opportunities/{opportunity_id}")
async def update_opportunity_status(
    opportunity_id: str,
    request: UpdateStatusRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = OpportunityScoreRepository(db)
    opp = await repo.get_by_id(opportunity_id)
    if not opp or opp.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Opportunity not found")
    updated = await repo.update(opportunity_id, status=request.status)
    return APIResponse(data={"id": updated.id, "status": updated.status}, message="Status updated")


# --- Decisions ---

@router.post("/decisions")
async def log_decision(
    request: LogDecisionRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    from datetime import date, timedelta
    repo = DecisionLogRepository(db)
    entry = await repo.create(
        user_id=str(user_id),
        decision=request.decision,
        why=request.why,
        expected_outcome=request.expected_outcome,
        review_date=date.today() + timedelta(days=request.review_days),
        tags=request.tags,
        goal_id=request.goal_id,
        status="pending_review"
    )
    return APIResponse(data={"id": entry.id, "review_date": str(entry.review_date)}, message="Decision logged")

@router.get("/decisions")
async def list_decisions(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = DecisionLogRepository(db)
    items = await repo.get_by_user(str(user_id))
    return APIResponse(data=[{
        "id": d.id, "decision": d.decision, "why": d.why,
        "expected_outcome": d.expected_outcome, "review_date": str(d.review_date),
        "actual_outcome": d.actual_outcome, "status": d.status,
        "tags": d.tags, "created_at": str(d.created_at)
    } for d in items])

@router.get("/decisions/pending-reviews")
async def get_pending_reviews(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = DecisionLogRepository(db)
    items = await repo.get_pending_reviews(str(user_id))
    return APIResponse(data=[{
        "id": d.id, "decision": d.decision, "why": d.why,
        "expected_outcome": d.expected_outcome, "review_date": str(d.review_date),
        "status": d.status
    } for d in items])

@router.patch("/decisions/{decision_id}")
async def update_decision(
    decision_id: str,
    request: UpdateDecisionRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = DecisionLogRepository(db)
    entry = await repo.get_by_id(decision_id)
    if not entry or entry.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Decision not found")
    kwargs = {}
    if request.actual_outcome is not None:
        kwargs["actual_outcome"] = request.actual_outcome
    if request.status is not None:
        kwargs["status"] = request.status
    updated = await repo.update(decision_id, **kwargs)
    return APIResponse(data={"id": updated.id, "status": updated.status}, message="Decision updated")

@router.post("/decisions/{decision_id}/review")
async def review_decision(
    decision_id: str,
    request: ReviewDecisionRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    from app.agents.strategic_brain import StrategicBrainAgent
    agent = StrategicBrainAgent()
    result = await agent.review_decision(str(user_id), decision_id, request.actual_outcome)
    return APIResponse(data=result.data, message=result.content)


# --- Experiments ---

@router.post("/experiments")
async def open_experiment(
    request: OpenExperimentRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = ExperimentRepository(db)
    exp = await repo.create(
        user_id=str(user_id),
        hypothesis=request.hypothesis,
        action=request.action,
        tags=request.tags,
        status="open"
    )
    return APIResponse(data={"id": exp.id}, message="Experiment opened")

@router.get("/experiments")
async def list_experiments(
    status: Optional[str] = None,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = ExperimentRepository(db)
    if status == "open":
        items = await repo.get_open(str(user_id))
    elif status == "closed":
        items = await repo.get_closed(str(user_id))
    else:
        items = await repo.get_by_user(str(user_id))
    return APIResponse(data=[{
        "id": e.id, "hypothesis": e.hypothesis, "action": e.action,
        "result": e.result, "learning": e.learning, "status": e.status,
        "tags": e.tags, "created_at": str(e.created_at),
        "closed_at": str(e.closed_at) if e.closed_at else None
    } for e in items])

@router.patch("/experiments/{experiment_id}/close")
async def close_experiment(
    experiment_id: str,
    request: CloseExperimentRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = ExperimentRepository(db)
    exp = await repo.get_by_id(experiment_id)
    if not exp or exp.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Experiment not found")
    updated = await repo.update(
        experiment_id,
        result=request.result,
        learning=request.learning,
        status="closed",
        closed_at=datetime.utcnow()
    )
    return APIResponse(data={"id": updated.id, "status": "closed"}, message="Experiment closed")

@router.get("/experiments/patterns")
async def get_experiment_patterns(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = ExperimentRepository(db)
    closed = await repo.get_closed(str(user_id))
    if not closed:
        return APIResponse(data=None, message="No closed experiments to analyze")

    experiments_text = "\n".join([
        f"- Hypothesis: {e.hypothesis} | Result: {e.result} | Learning: {e.learning}"
        for e in closed[:20]
    ])

    from app.llm import llm_router, TaskType
    response = await llm_router.generate(
        prompt=f"""Analyze these experiments and find patterns:

{experiments_text}

Identify: common themes, success patterns, failure patterns, and suggested next experiments.
Be concise.""",
        task_type=TaskType.COMPLEX_REASONING
    )
    return APIResponse(data={"analysis": response.content, "experiment_count": len(closed)})


# --- Distraction Rules ---

@router.post("/rules")
async def create_rule(
    request: CreateRuleRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = DistractionRuleRepository(db)
    rule = await repo.create(
        user_id=str(user_id),
        rule_name=request.rule_name,
        condition=request.condition,
        action=request.action,
        rule_type=request.rule_type,
        is_active=True
    )
    return APIResponse(data={"id": rule.id}, message="Rule created")

@router.get("/rules")
async def list_rules(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = DistractionRuleRepository(db)
    items = await repo.get_active_rules(str(user_id))
    return APIResponse(data=[{
        "id": r.id, "rule_name": r.rule_name, "condition": r.condition,
        "action": r.action, "rule_type": r.rule_type, "is_active": r.is_active
    } for r in items])

@router.patch("/rules/{rule_id}")
async def update_rule(
    rule_id: str,
    request: UpdateRuleRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = DistractionRuleRepository(db)
    rule = await repo.get_by_id(rule_id)
    if not rule or rule.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Rule not found")
    kwargs = {}
    if request.is_active is not None:
        kwargs["is_active"] = request.is_active
    if request.rule_name is not None:
        kwargs["rule_name"] = request.rule_name
    if request.condition is not None:
        kwargs["condition"] = request.condition
    if request.action is not None:
        kwargs["action"] = request.action
    updated = await repo.update(rule_id, **kwargs)
    return APIResponse(data={"id": updated.id, "is_active": updated.is_active}, message="Rule updated")

@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = DistractionRuleRepository(db)
    rule = await repo.get_by_id(rule_id)
    if not rule or rule.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Rule not found")
    await repo.delete(rule_id)
    return APIResponse(message="Rule deleted")


# --- Constraints ---

@router.get("/constraints")
async def get_constraints(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Identity).where(Identity.user_id == str(user_id), Identity.is_active == True)
    )
    identity = result.scalar_one_or_none()
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found. Create one first.")
    return APIResponse(data={
        "weekly_hours_available": identity.weekly_hours_available,
        "monthly_budget": identity.monthly_budget,
        "health_limits": identity.health_limits,
        "risk_tolerance": identity.risk_tolerance,
    })

@router.patch("/constraints")
async def update_constraints(
    request: UpdateConstraintsRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Identity).where(Identity.user_id == str(user_id), Identity.is_active == True)
    )
    identity = result.scalar_one_or_none()
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found. Create one first.")
    if request.risk_tolerance and request.risk_tolerance not in ("low", "medium", "high"):
        raise HTTPException(status_code=422, detail="risk_tolerance must be low, medium, or high")
    values = {}
    if request.weekly_hours_available is not None:
        values["weekly_hours_available"] = request.weekly_hours_available
    if request.monthly_budget is not None:
        values["monthly_budget"] = request.monthly_budget
    if request.health_limits is not None:
        values["health_limits"] = request.health_limits
    if request.risk_tolerance is not None:
        values["risk_tolerance"] = request.risk_tolerance
    if values:
        await db.execute(
            update(Identity).where(Identity.id == identity.id).values(**values)
        )
        await db.commit()
    return APIResponse(data=values, message="Constraints updated")


# --- Anti-Goals ---

@router.patch("/anti-goals")
async def update_anti_goals(
    request: AntiGoalsRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Identity).where(Identity.user_id == str(user_id), Identity.is_active == True)
    )
    identity = result.scalar_one_or_none()
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found. Create one first.")
    await db.execute(
        update(Identity).where(Identity.id == identity.id).values(anti_goals=request.anti_goals)
    )
    await db.commit()
    return APIResponse(data={"anti_goals": request.anti_goals}, message="Anti-goals updated")

@router.get("/anti-goals/check")
async def check_anti_goal_conflicts(
    proposal: str = Query(...),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    from app.agents.strategic_brain import StrategicBrainAgent
    agent = StrategicBrainAgent()
    conflicts = await agent.check_anti_goal_conflicts(str(user_id), proposal)
    return APIResponse(data={"conflicts": conflicts, "has_conflicts": len(conflicts) > 0})
