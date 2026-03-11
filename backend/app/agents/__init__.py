from .base import BaseAgent, AgentContext, AgentResponse


def __getattr__(name):
    """Lazy imports to avoid circular dependency with app.api."""
    if name == "ConversationOrchestrator":
        from .orchestrator import ConversationOrchestrator
        return ConversationOrchestrator
    if name == "Intent":
        from .orchestrator import Intent
        return Intent
    if name == "SafetyAgent":
        from .safety import SafetyAgent
        return SafetyAgent
    if name == "EmotionAgent":
        from .emotion import EmotionAgent
        return EmotionAgent
    if name == "MemoryAgent":
        from .memory import MemoryAgent
        return MemoryAgent
    if name == "PlannerAgent":
        from .planner import PlannerAgent
        return PlannerAgent
    if name == "InsightAgent":
        from .insight import InsightAgent
        return InsightAgent
    if name == "AcademyAgent":
        from .academy import AcademyAgent
        return AcademyAgent
    if name == "StrategicBrainAgent":
        from .strategic_brain import StrategicBrainAgent
        return StrategicBrainAgent
    raise AttributeError(f"module 'app.agents' has no attribute {name}")
