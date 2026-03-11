from fastapi import APIRouter, Depends
from uuid import UUID
from pydantic import BaseModel
from app.schemas.responses import APIResponse
from app.agents import AcademyAgent, AgentContext
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/academy", tags=["academy"])
academy_agent = AcademyAgent()

TOPICS = [
    {"slug": "rag", "title": "RAG: Retrieval-Augmented Generation", "category": "rag", "difficulty": "intermediate"},
    {"slug": "agents", "title": "AI Agents: Autonomous Systems", "category": "agents", "difficulty": "advanced"},
    {"slug": "embeddings", "title": "Embeddings: Text to Vectors", "category": "rag", "difficulty": "beginner"},
    {"slug": "llm", "title": "Large Language Models Explained", "category": "llm", "difficulty": "beginner"},
    {"slug": "prompting", "title": "Prompt Engineering", "category": "llm", "difficulty": "intermediate"},
    {"slug": "memory", "title": "AI Memory Systems", "category": "memory", "difficulty": "intermediate"},
]

class AskRequest(BaseModel):
    question: str

@router.get("/topics")
async def list_topics():
    return APIResponse(data=TOPICS)

@router.get("/topics/{slug}")
async def get_topic(slug: str):
    topic = next((t for t in TOPICS if t["slug"] == slug), None)
    if not topic:
        return APIResponse(data=None, message="Topic not found", success=False)
    return APIResponse(data=topic)

@router.post("/ask")
async def ask_academy(request: AskRequest, user_id: UUID = Depends(get_current_user_id)):
    context = AgentContext(user_id=str(user_id))
    response = await academy_agent.explain(request.question)
    return APIResponse(data={"answer": response.content, "topic": response.data.get("topic")})
