"""Email tracking and analytics."""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

TRACKING_DIR = Path(__file__).parent.parent / "data" / "email_tracking"
TRACKING_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class EmailRecord:
    """Track a single email."""
    id: str
    to_email: str
    subject: str
    body: str
    html_body: Optional[str]
    sent_at: Optional[str]
    status: str  # draft, sent, delivered, opened, replied, bounced
    job_id: Optional[int]
    recruiter_id: Optional[int]
    message_type: str  # cold_email, follow_up, connection_request
    follow_up_count: int
    last_follow_up_at: Optional[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "EmailRecord":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class EmailTracker:
    """Tracks sent emails, opens, replies, and follow-ups."""

    def __init__(self, tracking_dir: Path = TRACKING_DIR):
        self.tracking_dir = tracking_dir
        self.tracking_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, email_id: str) -> Path:
        return self.tracking_dir / f"{email_id}.json"

    def create_record(
        self,
        email_id: str,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        job_id: Optional[int] = None,
        recruiter_id: Optional[int] = None,
        message_type: str = "cold_email",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EmailRecord:
        """Create a new email tracking record."""
        record = EmailRecord(
            id=email_id,
            to_email=to_email,
            subject=subject,
            body=body,
            html_body=html_body,
            sent_at=None,
            status="draft",
            job_id=job_id,
            recruiter_id=recruiter_id,
            message_type=message_type,
            follow_up_count=0,
            last_follow_up_at=None,
            metadata=metadata or {},
        )
        self._save_record(record)
        return record

    def mark_sent(self, email_id: str, message_id: Optional[str] = None):
        """Mark email as sent."""
        record = self.get_record(email_id)
        if record:
            record.status = "sent"
            record.sent_at = datetime.utcnow().isoformat()
            if message_id:
                record.metadata["message_id"] = message_id
            self._save_record(record)

    def mark_opened(self, email_id: str):
        """Mark email as opened."""
        record = self.get_record(email_id)
        if record:
            record.status = "opened"
            record.metadata["opened_at"] = datetime.utcnow().isoformat()
            self._save_record(record)

    def mark_replied(self, email_id: str, reply_text: str = ""):
        """Mark email as replied."""
        record = self.get_record(email_id)
        if record:
            record.status = "replied"
            record.metadata["replied_at"] = datetime.utcnow().isoformat()
            record.metadata["reply_text"] = reply_text
            self._save_record(record)

    def mark_bounced(self, email_id: str, reason: str = ""):
        """Mark email as bounced."""
        record = self.get_record(email_id)
        if record:
            record.status = "bounced"
            record.metadata["bounce_reason"] = reason
            self._save_record(record)

    def record_follow_up(self, email_id: str):
        """Record a follow-up email."""
        record = self.get_record(email_id)
        if record:
            record.follow_up_count += 1
            record.last_follow_up_at = datetime.utcnow().isoformat()
            self._save_record(record)

    def get_record(self, email_id: str) -> Optional[EmailRecord]:
        """Get email record by ID."""
        filepath = self._get_file_path(email_id)
        if not filepath.exists():
            return None
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            return EmailRecord.from_dict(data)
        except Exception:
            return None

    def get_records_by_job(self, job_id: int) -> List[EmailRecord]:
        """Get all email records for a job."""
        records = []
        for filepath in self.tracking_dir.glob("*.json"):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                if data.get("job_id") == job_id:
                    records.append(EmailRecord.from_dict(data))
            except Exception:
                continue
        return records

    def get_records_by_status(self, status: str) -> List[EmailRecord]:
        """Get all email records with a specific status."""
        records = []
        for filepath in self.tracking_dir.glob("*.json"):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                if data.get("status") == status:
                    records.append(EmailRecord.from_dict(data))
            except Exception:
                continue
        return records

    def get_stats(self) -> Dict[str, Any]:
        """Get email tracking statistics."""
        stats = {
            "total": 0,
            "draft": 0,
            "sent": 0,
            "opened": 0,
            "replied": 0,
            "bounced": 0,
            "follow_ups": 0,
        }
        for filepath in self.tracking_dir.glob("*.json"):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                stats["total"] += 1
                status = data.get("status", "unknown")
                if status in stats:
                    stats[status] += 1
                stats["follow_ups"] += data.get("follow_up_count", 0)
            except Exception:
                continue

        if stats["sent"] > 0:
            stats["open_rate"] = round(stats["opened"] / stats["sent"] * 100, 1)
            stats["reply_rate"] = round(stats["replied"] / stats["sent"] * 100, 1)
        else:
            stats["open_rate"] = 0.0
            stats["reply_rate"] = 0.0

        return stats

    def _save_record(self, record: EmailRecord):
        """Save email record to disk."""
        filepath = self._get_file_path(record.id)
        with open(filepath, "w") as f:
            json.dump(record.to_dict(), f, indent=2, default=str)
