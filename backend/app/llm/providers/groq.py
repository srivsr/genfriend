"""
Groq LLM Provider - Fast & Cheap Llama inference
~5-20x cheaper than OpenAI/Claude with 10x faster inference
"""

import httpx
from typing import AsyncIterator
from .base import BaseLLMProvider, LLMResponse
from app.config import settings

GROQ_API_BASE = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.1-70b-versatile"

# Groq model options
GROQ_MODELS = {
    "fast": "llama-3.1-8b-instant",      # Fastest, cheapest
    "balanced": "llama-3.1-70b-versatile",  # Best quality/speed
    "mixtral": "mixtral-8x7b-32768",     # Good for long context
}


class GroqProvider(BaseLLMProvider):
    name = "groq"

    def __init__(self):
        self.api_key = settings.groq_api_key

    async def generate(
        self,
        prompt: str,
        context: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("Groq API key not configured")

        selected_model = model or DEFAULT_MODEL

        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{GROQ_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": selected_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )

            if response.status_code != 200:
                raise Exception(f"Groq API error: {response.text}")

            data = response.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})

            return LLMResponse(
                content=choice["message"]["content"],
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                model=selected_model
            )

    async def stream(
        self,
        prompt: str,
        context: str | None = None,
        model: str | None = None
    ) -> AsyncIterator[str]:
        if not self.api_key:
            raise ValueError("Groq API key not configured")

        selected_model = model or DEFAULT_MODEL

        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{GROQ_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": selected_model,
                    "messages": messages,
                    "stream": True
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        import json
                        data = json.loads(line[6:])
                        if data["choices"][0].get("delta", {}).get("content"):
                            yield data["choices"][0]["delta"]["content"]
