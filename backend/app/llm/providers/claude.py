import logging
from anthropic import AsyncAnthropic
from typing import AsyncIterator
from .base import BaseLLMProvider, LLMResponse
from app.config import settings

logger = logging.getLogger(__name__)

class ClaudeProvider(BaseLLMProvider):
    name = "claude"

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key, timeout=60.0)
        self.default_model = "claude-sonnet-4-20250514"

    async def generate(self, prompt: str, context: str | None = None, model: str | None = None, temperature: float = 0.7, max_tokens: int = 2000) -> LLMResponse:
        model = model or self.default_model
        messages = [{"role": "user", "content": prompt}]

        kwargs = dict(model=model, max_tokens=max_tokens, temperature=temperature, messages=messages)
        if context:
            kwargs["system"] = context

        response = await self.client.messages.create(**kwargs)
        logger.info(f"Claude response: model={model} tokens={response.usage.input_tokens}+{response.usage.output_tokens}")
        return LLMResponse(
            content=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=model
        )

    async def stream(self, prompt: str, context: str | None = None, model: str | None = None) -> AsyncIterator[str]:
        model = model or self.default_model
        messages = [{"role": "user", "content": prompt}]

        kwargs = dict(model=model, max_tokens=2000, messages=messages)
        if context:
            kwargs["system"] = context

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text
