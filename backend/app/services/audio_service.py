"""
Audio Service - Multi-Provider STT and TTS
Supports Groq (cheaper) and OpenAI as fallback
"""

import os
import httpx
from typing import Optional
from fastapi import UploadFile, HTTPException
from app.config import settings

ALLOWED_AUDIO_TYPES = {
    "audio/webm", "audio/ogg", "audio/mpeg", "audio/mp3",
    "audio/wav", "audio/x-wav", "audio/m4a", "audio/mp4"
}
MAX_FILE_SIZE_MB = 25


class AudioService:
    """Multi-provider Audio Service for STT and TTS."""

    def __init__(self):
        self.openai_key = settings.openai_api_key
        self.groq_key = settings.groq_api_key
        self.stt_provider = settings.stt_provider
        self.tts_provider = settings.tts_provider

    async def transcribe_audio(self, file: UploadFile) -> str:
        """Transcribe audio - uses Groq by default (3x cheaper)."""
        content_type = file.content_type or ""
        if content_type not in ALLOWED_AUDIO_TYPES:
            ext = os.path.splitext(file.filename or "")[1].lower()
            if ext not in {".webm", ".ogg", ".mp3", ".wav", ".m4a", ".mp4"}:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported audio format. Allowed: webm, ogg, mp3, wav, m4a"
                )

        audio_bytes = await file.read()

        if len(audio_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"Audio file too large. Max: {MAX_FILE_SIZE_MB}MB")

        filename = file.filename or "audio.webm"

        # Use configured provider
        if self.stt_provider == "groq" and self.groq_key:
            return await self._transcribe_groq(audio_bytes, filename)
        elif self.openai_key:
            return await self._transcribe_openai(audio_bytes, filename, content_type)
        else:
            raise HTTPException(status_code=500, detail="No STT provider configured")

    async def _transcribe_groq(self, audio_bytes: bytes, filename: str) -> str:
        """Groq Whisper - faster and ~3x cheaper than OpenAI."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.groq_key}"},
                    files={"file": (filename, audio_bytes)},
                    data={"model": "whisper-large-v3"}
                )

                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=f"Groq STT failed: {response.text}")

                return response.json().get("text", "")

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Transcription timed out")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Groq STT error: {str(e)}")

    async def _transcribe_openai(self, audio_bytes: bytes, filename: str, content_type: str) -> str:
        """OpenAI Whisper - fallback option."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.openai_key}"},
                    files={
                        "file": (filename, audio_bytes, content_type or "audio/webm"),
                        "model": (None, "whisper-1"),
                    }
                )

                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=f"OpenAI STT failed: {response.text}")

                return response.json().get("text", "")

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Transcription timed out")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OpenAI STT error: {str(e)}")

    async def synthesize_speech(self, text: str, voice: Optional[str] = None, response_format: str = "mp3") -> bytes:
        """Convert text to speech - OpenAI only (Groq has no TTS yet)."""
        if not self.openai_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured for TTS")

        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        if len(text) > 4096:
            text = text[:4096]

        selected_voice = voice or "alloy"

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers={
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "tts-1",
                        "input": text,
                        "voice": selected_voice,
                        "response_format": response_format
                    }
                )

                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=f"TTS failed: {response.text}")

                return response.content

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="TTS timed out")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")


audio_service = AudioService()
