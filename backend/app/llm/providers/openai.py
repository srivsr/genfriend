import logging
from openai import AsyncOpenAI
from typing import AsyncIterator
from .base import BaseLLMProvider, LLMResponse
from app.config import settings

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLMProvider):
    name = "openai"

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=60.0)
        self.default_model = "gpt-4o"

    async def generate(self, prompt: str, context: str | None = None, model: str | None = None, temperature: float = 0.7, max_tokens: int = 2000) -> LLMResponse:
        model = model or self.default_model
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        logger.info(f"OpenAI response: model={model} tokens={response.usage.prompt_tokens}+{response.usage.completion_tokens}")
        return LLMResponse(
            content=response.choices[0].message.content,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            model=model
        )

    async def stream(self, prompt: str, context: str | None = None, model: str | None = None) -> AsyncIterator[str]:
        model = model or self.default_model
        messages = [{"role": "user", "content": prompt}]
        if context:
            messages.insert(0, {"role": "system", "content": context})

        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
