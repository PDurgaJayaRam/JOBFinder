"""Outreach automation module."""

from outreach.email_sender import EmailSender, EmailConfig, EmailResult
from outreach.email_tracker import EmailTracker, EmailRecord
from outreach.follow_up_manager import FollowUpManager
from outreach.orchestrator import OutreachOrchestrator

__all__ = [
    "EmailSender",
    "EmailConfig",
    "EmailResult",
    "EmailTracker",
    "EmailRecord",
    "FollowUpManager",
    "OutreachOrchestrator",
]
