import logging
import time
from enum import Enum
from typing import Optional
from .providers import BaseLLMProvider, ClaudeProvider, OpenAIProvider, GroqProvider, LLMResponse
from app.services.cost_tracker import CostTracker
from app.services.subscription_service import get_llm_model_for_tier
from app.config import settings

logger = logging.getLogger(__name__)

class TaskType(Enum):
    CLASSIFICATION = "classification"
    GENERATION = "generation"
    COMPLEX_REASONING = "complex_reasoning"
    EMBEDDING = "embedding"

class LLMRouter:
    def __init__(self):
        self.providers: dict[str, BaseLLMProvider] = {
            "claude": ClaudeProvider(),
            "openai": OpenAIProvider(),
            "groq": GroqProvider()
        }
        # Use configured provider (groq is cheapest)
        self.default = settings.llm_provider if settings.llm_provider in self.providers else "groq"
        self.cost_tracker = CostTracker()

    async def generate(
        self,
        prompt: str,
        context: str | None = None,
        model_preference: str | None = None,
        task_type: TaskType = TaskType.GENERATION,
        user_id: str | None = None,
        subscription_tier: str | None = None
    ) -> LLMResponse:
        provider, model = self._select_model(task_type, model_preference, subscription_tier)

        start = time.time()
        try:
            response = await provider.generate(prompt=prompt, context=context, model=model)
            elapsed_ms = int((time.time() - start) * 1000)
            logger.info(f"LLM generate: provider={provider.name} model={response.model} task={task_type.value} tokens={response.input_tokens}+{response.output_tokens} latency={elapsed_ms}ms")
            if user_id:
                await self.cost_tracker.track(
                    user_id=user_id,
                    model=response.model,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    request_type=task_type.value
                )
            return response
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            logger.error(f"LLM generate failed: provider={provider.name} task={task_type.value} latency={elapsed_ms}ms error={e}")
            return await self._fallback_generate(prompt, context, task_type)

    def _select_model(
        self,
        task_type: TaskType,
        preference: str | None = None,
        subscription_tier: str | None = None
    ) -> tuple[BaseLLMProvider, Optional[str]]:
        # If subscription tier provided, use tier-based model selection
        if subscription_tier:
            model = get_llm_model_for_tier(subscription_tier)
            return self.providers["openai"], model

        if preference and preference in self.providers:
            return self.providers[preference], None

        # Use configured default provider for all tasks
        match task_type:
            case TaskType.CLASSIFICATION:
                return self.providers[self.default], None
            case TaskType.GENERATION:
                return self.providers[self.default], None
            case TaskType.COMPLEX_REASONING:
                # Use OpenAI GPT-4o for complex reasoning
                return self.providers["openai"], "gpt-4o"
            case _:
                return self.providers[self.default], None

    async def _fallback_generate(self, prompt: str, context: str | None, task_type: TaskType) -> LLMResponse:
        logger.warning(f"Falling back to OpenAI for task={task_type.value}")
        provider = self.providers["openai"]
        return await provider.generate(prompt=prompt, context=context)

llm_router = LLMRouter()


async def get_llm_response(
    message: str,
    system_prompt: str = None,
    max_tokens: int = 500,
    subscription_tier: str = None
) -> str:
    """Simple helper to get LLM response for voice chat."""
    prompt = message
    if system_prompt:
        prompt = f"{system_prompt}\n\nUser: {message}\n\nAssistant:"

    response = await llm_router.generate(
        prompt=prompt,
        task_type=TaskType.GENERATION,
        subscription_tier=subscription_tier
    )
    return response.content
