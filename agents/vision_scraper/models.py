"""Core data models and type definitions for vision-guided scraping."""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, HttpUrl


class ActionType(str, Enum):
    """Available navigation actions for vision-guided scraping."""
    CLICK = "CLICK"
    TYPE = "TYPE"
    SCROLL = "SCROLL"
    WAIT = "WAIT"
    GOAL_ACHIEVED = "GOAL_ACHIEVED"
    ERROR = "ERROR"


class NavigationStatus(str, Enum):
    """Status of a navigation operation."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    TIMEOUT = "TIMEOUT"


class ExtractionMethod(str, Enum):
    """Method used for job data extraction."""
    JAVASCRIPT = "JAVASCRIPT"
    VISION = "VISION"
    HYBRID = "HYBRID"


class ActionDecision(BaseModel):
    """Decision made by the vision model for the next navigation action."""
    action_type: ActionType
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    x_coordinate: Optional[int] = None
    y_coordinate: Optional[int] = None
    text: Optional[str] = None
    scroll_direction: Optional[str] = None
    scroll_amount: Optional[int] = None
    wait_duration: Optional[float] = None
    error_message: Optional[str] = None

    @validator("x_coordinate", "y_coordinate")
    def validate_coordinates(cls, v, values):
        if values.get("action_type") in [ActionType.CLICK, ActionType.TYPE]:
            if v is None:
                raise ValueError("Coordinates required for CLICK/TYPE actions")
            if v < 0:
                raise ValueError("Coordinates must be non-negative")
        return v

    @validator("text")
    def validate_text(cls, v, values):
        if values.get("action_type") == ActionType.TYPE:
            if not v or not v.strip():
                raise ValueError("Text required for TYPE actions")
        return v

    @validator("scroll_direction")
    def validate_scroll_direction(cls, v, values):
        if values.get("action_type") == ActionType.SCROLL:
            if v not in ["up", "down", "left", "right"]:
                raise ValueError("Scroll direction must be up/down/left/right")
        return v

    @validator("scroll_amount")
    def validate_scroll_amount(cls, v, values):
        if values.get("action_type") == ActionType.SCROLL:
            if v is None or v <= 0:
                raise ValueError("Positive scroll amount required")
        return v

    @validator("wait_duration")
    def validate_wait_duration(cls, v, values):
        if values.get("action_type") == ActionType.WAIT:
            if v is None or v <= 0:
                raise ValueError("Positive wait duration required")
        return v


class ActionResult(BaseModel):
    """Result of executing an action."""
    success: bool
    action_type: ActionType
    message: str
    execution_time_ms: int
    error: Optional[str] = None


class PageState(BaseModel):
    """Current state of the browser page."""
    url: str
    title: str
    is_loaded: bool
    has_popup: bool = False
    popup_type: Optional[str] = None
    screenshot_base64: Optional[str] = None
    viewport_width: int
    viewport_height: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class JobData(BaseModel):
    """Extracted job data from a job portal."""
    title: str
    company: str
    location: str
    description: Optional[str] = None
    source: str
    source_url: str
    apply_url: Optional[str] = None
    salary: Optional[str] = None
    job_type: Optional[str] = None
    experience_required: Optional[str] = None
    skills: Optional[List[str]] = None
    posted_date: Optional[str] = None
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    extraction_method: ExtractionMethod = ExtractionMethod.JAVASCRIPT

    @validator("title", "company", "location")
    def validate_required_fields(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @validator("source_url", "apply_url")
    def validate_urls(cls, v):
        if v is not None:
            try:
                HttpUrl(v)
            except Exception:
                raise ValueError("Invalid URL format")
        return v


class ScrapingResult(BaseModel):
    """Result of a scraping operation."""
    portal_name: str
    status: NavigationStatus
    jobs: List[JobData] = []
    steps_taken: int = 0
    actions_taken: List[ActionDecision] = []
    screenshots_taken: int = 0
    extraction_method: ExtractionMethod = ExtractionMethod.JAVASCRIPT
    time_elapsed_ms: int = 0
    error_message: Optional[str] = None


class NavigationResult(BaseModel):
    """Result of a navigation operation."""
    portal_url: str
    status: NavigationStatus
    steps_taken: int
    actions: List[ActionDecision] = []
    screenshots_taken: int
    time_elapsed_ms: int
    error_message: Optional[str] = None
