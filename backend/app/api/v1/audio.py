"""
Audio Router - Voice Chat Endpoints for Dictation
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional
from pydantic import BaseModel
import io
import base64

from app.dependencies import get_current_user_id
from app.services.audio_service import audio_service
from app.llm.router import get_llm_response

router = APIRouter(prefix="/audio", tags=["Audio"])


class VoiceChatResponse(BaseModel):
    transcript: str
    reply_text: str
    audio: Optional[str] = None


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None


class TranscribeResponse(BaseModel):
    transcript: str


VOICE_SYSTEM_PROMPT = """You are Gen-Friend, a warm and motivating AI productivity companion.

VOICE INTERACTION RULES:
- Keep answers SHORT (1-2 sentences max)
- Sound friendly, direct, and natural
- Avoid bullet lists - speak conversationally
- If user needs detailed info, say "Would you like me to explain more?"
- Use simple language that sounds good when spoken aloud
- Be encouraging but concise

You help users with career planning, goal setting, daily tasks, and skill development."""


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_only(
    audio: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Transcribe audio to text only (no AI response).
    Use this for dictation into text fields.
    """
    transcript = await audio_service.transcribe_audio(audio)

    if not transcript.strip():
        raise HTTPException(status_code=400, detail="Could not transcribe audio. Please speak clearly and try again.")

    return TranscribeResponse(transcript=transcript)


@router.post("/voice-chat", response_model=VoiceChatResponse)
async def voice_chat(
    audio: UploadFile = File(...),
    mode: Optional[str] = Form(default="chat"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Process voice input and return AI response (text only).
    """
    transcript = await audio_service.transcribe_audio(audio)

    if not transcript.strip():
        raise HTTPException(status_code=400, detail="Could not transcribe audio. Please speak clearly and try again.")

    reply = await get_llm_response(
        message=transcript,
        system_prompt=VOICE_SYSTEM_PROMPT,
        max_tokens=150
    )

    return VoiceChatResponse(
        transcript=transcript,
        reply_text=reply,
        audio=None
    )


@router.post("/voice-chat-with-audio")
async def voice_chat_with_audio(
    audio: UploadFile = File(...),
    mode: Optional[str] = Form(default="chat"),
    include_tts: bool = Form(default=True),
    history: Optional[str] = Form(default=None),
    user_id: str = Depends(get_current_user_id)
):
    """
    Process voice input and return AI response with optional TTS audio.
    """
    transcript = await audio_service.transcribe_audio(audio)

    if not transcript.strip():
        raise HTTPException(status_code=400, detail="Could not transcribe audio. Please speak clearly and try again.")

    reply = await get_llm_response(
        message=transcript,
        system_prompt=VOICE_SYSTEM_PROMPT,
        max_tokens=150
    )

    audio_base64 = None
    if include_tts:
        audio_bytes = await audio_service.synthesize_speech(text=reply, response_format="mp3")
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    return {
        "transcript": transcript,
        "reply_text": reply,
        "audio": audio_base64,
        "audio_format": "mp3" if audio_base64 else None
    }


@router.post("/tts")
async def text_to_speech(
    request: TTSRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Convert text to speech using OpenAI TTS."""
    audio_bytes = await audio_service.synthesize_speech(
        text=request.text,
        voice=request.voice,
        response_format="mp3"
    )

    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=speech.mp3"}
    )
