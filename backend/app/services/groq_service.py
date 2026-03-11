"""
Groq Service - Fast & Cheap STT and LLM
Uses Groq's LPU infrastructure for Whisper and Llama models
"""

import httpx
from typing import Optional
from fastapi import HTTPException
from app.config import settings

GROQ_API_BASE = "https://api.groq.com/openai/v1"
GROQ_WHISPER_MODEL = "whisper-large-v3"
GROQ_LLM_MODEL = "llama-3.1-70b-versatile"


class GroqService:
    """Groq API Service for STT and LLM."""

    def __init__(self):
        self.api_key = settings.groq_api_key
        self.whisper_model = GROQ_WHISPER_MODEL
        self.llm_model = GROQ_LLM_MODEL

    async def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.webm") -> str:
        """Transcribe audio using Groq Whisper (faster & cheaper than OpenAI)."""
        if not self.api_key:
            raise HTTPException(status_code=500, detail="Groq API key not configured")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{GROQ_API_BASE}/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files={"file": (filename, audio_bytes)},
                    data={"model": self.whisper_model}
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Groq transcription failed: {response.text}"
                    )

                result = response.json()
                return result.get("text", "")

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Groq transcription timed out")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Groq transcription error: {str(e)}")

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        system_prompt: Optional[str] = None
    ) -> str:
        """Chat completion using Groq Llama (5-20x cheaper than OpenAI/Claude)."""
        if not self.api_key:
            raise HTTPException(status_code=500, detail="Groq API key not configured")

        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{GROQ_API_BASE}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.llm_model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Groq chat failed: {response.text}"
                    )

                result = response.json()
                return result["choices"][0]["message"]["content"]

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Groq chat timed out")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Groq chat error: {str(e)}")

    async def chat_with_context(
        self,
        user_message: str,
        context: str,
        conversation_history: list[dict] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Chat with additional context (for RAG, identity-aware responses)."""

        default_system = """You are Gen-Friend, a supportive AI companion focused on career growth,
skill development, and daily productivity. Be warm, encouraging, and practical.
Keep responses concise but helpful."""

        full_system = system_prompt or default_system
        if context:
            full_system += f"\n\nContext:\n{context}"

        messages = []
        if conversation_history:
            messages.extend(conversation_history[-10:])  # Last 10 messages
        messages.append({"role": "user", "content": user_message})

        return await self.chat(messages, system_prompt=full_system)


groq_service = GroqService()
