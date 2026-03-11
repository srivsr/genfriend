import json
import logging
from dataclasses import dataclass
from .base import BaseAgent, AgentContext, AgentResponse
from app.llm import TaskType

logger = logging.getLogger(__name__)

CRISIS_KEYWORDS = ["suicide", "kill myself", "end it all", "self-harm", "want to die", "hurt myself"]

CRISIS_RESPONSE = """I hear that you're going through something really difficult. I care about you, and I want you to know you're not alone.

I'm an AI and not equipped to provide the support you deserve right now. Please reach out to someone who can help:

India: iCall - 9152987821
US: 988 Suicide & Crisis Lifeline
International: findahelpline.com

Would you like to talk about what's been on your mind? I'm here to listen."""

@dataclass
class SafetyCheck:
    requires_intervention: bool
    response: str | None = None
    severity: str = "low"

class SafetyAgent(BaseAgent):
    name = "safety"
    description = "Ensures safe, appropriate responses with crisis detection"

    async def process(self, message: str, context: AgentContext) -> AgentResponse:
        check = await self.check(message)
        if check.requires_intervention:
            return AgentResponse(content=check.response, metadata={"severity": check.severity})
        return AgentResponse(content="", metadata={"safe": True})

    async def check(self, message: str) -> SafetyCheck:
        lower_msg = message.lower()
        for keyword in CRISIS_KEYWORDS:
            if keyword in lower_msg:
                return SafetyCheck(requires_intervention=True, response=CRISIS_RESPONSE, severity="high")

        prompt = f"""Analyze this message for safety concerns. Rate concern level 0-1.
Categories: self-harm, harmful-advice, inappropriate-content, none

Message: {message}

Respond as JSON: {{"concern_level": 0.0, "concern_type": "none"}}"""

        try:
            response = await self._generate(prompt, task_type=TaskType.CLASSIFICATION)
        except Exception:
            return SafetyCheck(requires_intervention=False)

        try:
            parsed = json.loads(response)
            concern_level = float(parsed.get("concern_level", 0))
            if concern_level >= 0.7:
                logger.warning(f"Safety concern detected: level={concern_level}, type={parsed.get('concern_type')}")
                return SafetyCheck(requires_intervention=True, response="I want to help, but I'm not the right resource for this. Please consider speaking with a professional.", severity="medium")
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

        return SafetyCheck(requires_intervention=False)

    def filter_output(self, response: str) -> str:
        lower = response.lower()
        for keyword in CRISIS_KEYWORDS:
            if keyword in lower:
                logger.warning("Output filter triggered: crisis keyword in LLM output")
                return "I want to make sure I'm being helpful and safe. Could you tell me more about what you're looking for?"

        boundary_violations = [
            "medical advice", "i recommend taking", "you should take this medication",
            "investment advice", "buy this stock", "financial planning",
            "as a therapist", "diagnosis is", "prescription",
        ]
        for phrase in boundary_violations:
            if phrase in lower:
                logger.warning(f"Output filter triggered: boundary violation '{phrase}'")
                return f"{response}\n\n(Note: I'm an AI companion focused on career and personal growth. For specialized advice on health, finance, or therapy, please consult a qualified professional.)"

        return response
