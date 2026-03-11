from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator

@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int
    model: str

class BaseLLMProvider(ABC):
    name: str

    @abstractmethod
    async def generate(self, prompt: str, context: str | None = None, model: str | None = None, temperature: float = 0.7, max_tokens: int = 2000) -> LLMResponse:
        pass

    @abstractmethod
    async def stream(self, prompt: str, context: str | None = None, model: str | None = None) -> AsyncIterator[str]:
        pass
