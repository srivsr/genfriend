import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from app.llm import llm_router, TaskType

logger = logging.getLogger(__name__)

@dataclass
class AgentContext:
    user_id: str
    conversation_history: list[dict] = None
    metadata: dict = None

    def __post_init__(self):
        self.conversation_history = self.conversation_history or []
        self.metadata = self.metadata or {}

@dataclass
class AgentResponse:
    content: str
    data: Any = None
    confidence: float = 1.0
    metadata: dict = None

class BaseAgent(ABC):
    name: str
    description: str

    def __init__(self):
        self.llm = llm_router

    @abstractmethod
    async def process(self, message: str, context: AgentContext) -> AgentResponse:
        pass

    async def _generate(self, prompt: str, context: str | None = None, task_type: TaskType = TaskType.GENERATION) -> str:
        start = time.time()
        try:
            response = await self.llm.generate(prompt=prompt, context=context, task_type=task_type)
            elapsed_ms = int((time.time() - start) * 1000)
            logger.info(f"Agent {self.name} generated response: task={task_type.value} latency={elapsed_ms}ms")
            return response.content
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            logger.error(f"Agent {self.name} generation failed: task={task_type.value} latency={elapsed_ms}ms error={e}")
            raise
