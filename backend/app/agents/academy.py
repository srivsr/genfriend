from .base import BaseAgent, AgentContext, AgentResponse
from app.llm import TaskType

AI_TOPICS = {
    "rag": "Retrieval-Augmented Generation combines search with LLM generation for accurate, grounded responses.",
    "agents": "AI agents are systems that can plan, reason, and use tools to accomplish complex tasks autonomously.",
    "embeddings": "Embeddings convert text into numerical vectors that capture semantic meaning for similarity search.",
    "llm": "Large Language Models are neural networks trained on vast text data to understand and generate human language.",
    "prompting": "Prompt engineering is the art of crafting effective instructions to get optimal responses from AI models.",
    "memory": "AI memory systems store and retrieve context to maintain coherent, personalized conversations.",
    "fine-tuning": "Fine-tuning adapts pre-trained models to specific tasks or domains using additional training data.",
}

class AcademyAgent(BaseAgent):
    name = "academy"
    description = "Explains AI concepts in simple, relatable terms"

    async def process(self, message: str, context: AgentContext) -> AgentResponse:
        return await self.explain(message)

    async def explain(self, query: str) -> AgentResponse:
        topic = self._identify_topic(query)
        base_knowledge = AI_TOPICS.get(topic, "")

        prompt = f"""Explain this AI concept to a college student in India:

Query: {query}
{f"Base context: {base_knowledge}" if base_knowledge else ""}

Guidelines:
- Use simple analogies from daily life
- Keep it under 150 words
- Include a practical example
- Make it engaging and interesting
- End with a thought-provoking question or next learning step"""

        response = await self._generate(prompt, task_type=TaskType.GENERATION)
        return AgentResponse(content=response, data={"topic": topic})

    def _identify_topic(self, query: str) -> str:
        lower = query.lower()
        for topic in AI_TOPICS:
            if topic in lower:
                return topic
        return "general"
