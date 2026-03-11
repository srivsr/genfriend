from fastapi import APIRouter, Depends
from uuid import UUID
from app.schemas.responses import APIResponse
from app.agents import InsightAgent, AgentContext
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/insights", tags=["insights"])
insight_agent = InsightAgent()

@router.get("/weekly")
async def weekly_summary(user_id: UUID = Depends(get_current_user_id)):
    context = AgentContext(user_id=str(user_id))
    response = await insight_agent.analyze(str(user_id), "Give me my weekly summary and patterns")
    return APIResponse(data={"summary": response.content, "insights": response.data})

@router.get("/patterns")
async def patterns(user_id: UUID = Depends(get_current_user_id)):
    context = AgentContext(user_id=str(user_id))
    response = await insight_agent.analyze(str(user_id), "What patterns do you see in my behavior?")
    return APIResponse(data={"analysis": response.content})

@router.get("/mood")
async def mood_trends(user_id: UUID = Depends(get_current_user_id)):
    return APIResponse(data={"trends": [], "average": "neutral"})
