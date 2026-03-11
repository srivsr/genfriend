from .cost_tracker import CostTracker
from .auth import AuthService
from .embedding_service import EmbeddingService


def __getattr__(name):
    """Lazy imports to avoid circular dependency with app.llm."""
    if name == "PatternDetector":
        from .pattern_detector import PatternDetector
        return PatternDetector
    if name == "ExperienceService":
        from .experience_service import ExperienceService
        return ExperienceService
    if name == "UniversalSkillEngine":
        from .skill_engine import UniversalSkillEngine
        return UniversalSkillEngine
    if name in ("DailySnapshotService", "NudgeService"):
        from .snapshot_service import DailySnapshotService, NudgeService
        return DailySnapshotService if name == "DailySnapshotService" else NudgeService
    if name in ("PortfolioService", "InterviewTwinService"):
        from .portfolio_service import PortfolioService, InterviewTwinService
        return PortfolioService if name == "PortfolioService" else InterviewTwinService
    raise AttributeError(f"module 'app.services' has no attribute {name}")
