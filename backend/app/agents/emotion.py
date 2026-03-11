from dataclasses import dataclass
from .base import BaseAgent, AgentContext, AgentResponse
from app.llm import TaskType

@dataclass
class EmotionalState:
    primary: str
    intensity: int
    confidence: float

@dataclass
class ToneGuidance:
    style: str
    avoid: str
    suggest: str

class EmotionAgent(BaseAgent):
    name = "emotion"
    description = "Detects emotional state and adapts tone"

    async def process(self, message: str, context: AgentContext) -> AgentResponse:
        state = await self.detect(message, context)
        guidance = self.get_tone_guidance(state)
        return AgentResponse(content="", data={"state": state, "guidance": guidance})

    async def detect(self, message: str, context: AgentContext) -> EmotionalState:
        recent = context.conversation_history[-5:] if context.conversation_history else []
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in recent])

        prompt = f"""Detect the emotional state from this message.
Categories: positive, neutral, stressed, overwhelmed, sad, excited, anxious, frustrated

Recent conversation:
{history_text}

Current message: {message}

Respond as: emotion|intensity(1-5)|confidence(0-1)
Example: stressed|4|0.8"""

        try:
            response = await self._generate(prompt, task_type=TaskType.CLASSIFICATION)
            parts = response.strip().split("|")
            return EmotionalState(primary=parts[0], intensity=int(parts[1]), confidence=float(parts[2]))
        except Exception:
            return EmotionalState(primary="neutral", intensity=3, confidence=0.5)

    def get_tone_guidance(self, state: EmotionalState) -> ToneGuidance:
        if state.primary in ["stressed", "overwhelmed", "anxious"]:
            return ToneGuidance(
                style="calm, supportive, shorter responses",
                avoid="overwhelming with options, adding pressure",
                suggest="offer to simplify, acknowledge difficulty"
            )
        elif state.primary == "sad":
            return ToneGuidance(
                style="warm, empathetic, gentle",
                avoid="toxic positivity, dismissing feelings",
                suggest="validate feelings, offer presence"
            )
        elif state.primary == "frustrated":
            return ToneGuidance(
                style="understanding, solution-focused",
                avoid="being dismissive, over-explaining",
                suggest="acknowledge frustration, offer concrete help"
            )
        elif state.primary in ["positive", "excited"]:
            return ToneGuidance(
                style="energetic, encouraging",
                avoid="dampening enthusiasm",
                suggest="match energy, build momentum"
            )
        return ToneGuidance(style="balanced, friendly", avoid="extremes", suggest="be helpful and clear")
