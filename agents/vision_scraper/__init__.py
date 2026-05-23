"""Vision-guided adaptive scraping module."""

from .models import (
    ActionType,
    NavigationStatus,
    ExtractionMethod,
    ActionDecision,
    ActionResult,
    PageState,
    JobData,
    ScrapingResult,
    NavigationResult,
)
from .rate_limiter import RateLimiter
from .multi_provider_client import MultiProviderAIClient
from .portal_adapter import PortalAdapter
from .hybrid_extractor import HybridExtractor
from .config import ScrapingConfig

__all__ = [
    "ActionType",
    "NavigationStatus",
    "ExtractionMethod",
    "ActionDecision",
    "ActionResult",
    "PageState",
    "JobData",
    "ScrapingResult",
    "NavigationResult",
    "RateLimiter",
    "MultiProviderAIClient",
    "PortalAdapter",
    "HybridExtractor",
    "ScrapingConfig",
]


def __getattr__(name):
    if name == "VisionAgent":
        from .vision_agent import VisionAgent
        return VisionAgent
    if name == "ScrapingOrchestrator":
        from .scraping_orchestrator import ScrapingOrchestrator
        return ScrapingOrchestrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
