"""Outreach automation orchestrator."""
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from outreach.email_sender import EmailSender, EmailConfig, EmailResult
from outreach.email_tracker import EmailTracker
from outreach.follow_up_manager import FollowUpManager
from agents.networking.messages import NetworkingAgent

logger = logging.getLogger(__name__)


class OutreachOrchestrator:
    """Orchestrates email outreach campaigns."""

    def __init__(
        self,
        email_config: Optional[EmailConfig] = None,
    ):
        self.email_sender = EmailSender(config=email_config)
        self.email_tracker = EmailTracker()
        self.networking = NetworkingAgent()
        self.follow_up_manager = FollowUpManager(
            email_sender=self.email_sender,
            email_tracker=self.email_tracker,
            networking_agent=self.networking,
        )

    async def send_outreach_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        job_id: Optional[int] = None,
        recruiter_id: Optional[int] = None,
        from_name: str = "",
        auto_follow_up: bool = True,
    ) -> Dict[str, Any]:
        """Send a single outreach email and track it."""
        email_id = str(uuid.uuid4())[:12]

        self.email_tracker.create_record(
            email_id=email_id,
            to_email=to_email,
            subject=subject,
            body=body,
            html_body=html_body,
            job_id=job_id,
            recruiter_id=recruiter_id,
            message_type="cold_email",
        )

        result = self.email_sender.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            html_body=html_body,
            from_name=from_name,
        )

        if result.success:
            self.email_tracker.mark_sent(email_id, result.message_id)
            logger.info(f"Outreach email sent: {email_id} to {to_email}")
        else:
            self.email_tracker.mark_bounced(email_id, result.error)
            logger.error(f"Outreach email failed: {email_id} - {result.error}")

        return {
            "email_id": email_id,
            "success": result.success,
            "error": result.error,
            "auto_follow_up": auto_follow_up,
        }

    async def send_job_outreach(
        self,
        job: Dict[str, Any],
        recruiter: Dict[str, Any],
        resume_summary: str,
        from_name: str = "",
    ) -> Dict[str, Any]:
        """Generate and send outreach email for a specific job and recruiter."""
        to_email = recruiter.get("email", "")
        if not to_email:
            return {"success": False, "error": "No email address for recruiter"}

        message = await self.networking.generate_job_outreach(
            job=job,
            resume_summary=resume_summary,
            recipient_name=recruiter.get("name", ""),
        )

        subject = f"Application: {job.get('title', '')} - {from_name or 'Interested Candidate'}"

        return await self.send_outreach_email(
            to_email=to_email,
            subject=subject,
            body=message,
            job_id=job.get("id"),
            recruiter_id=recruiter.get("id"),
            from_name=from_name,
        )

    async def process_follow_ups(
        self,
        jobs_data: Dict[int, Dict[str, Any]],
        resume_summary: str,
        from_name: str = "",
    ) -> List[Dict[str, Any]]:
        """Process pending follow-ups."""
        return await self.follow_up_manager.process_all_follow_ups(
            jobs_data=jobs_data,
            resume_summary=resume_summary,
            from_name=from_name,
        )

    def get_email_stats(self) -> Dict[str, Any]:
        """Get email outreach statistics."""
        return self.email_tracker.get_stats()

    def get_email_history(self, job_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get email history, optionally filtered by job."""
        if job_id:
            records = self.email_tracker.get_records_by_job(job_id)
        else:
            records = []
            for status in ["draft", "sent", "opened", "replied", "bounced"]:
                records.extend(self.email_tracker.get_records_by_status(status))

        return [r.to_dict() for r in records]

    def get_email_record(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific email record."""
        record = self.email_tracker.get_record(email_id)
        return record.to_dict() if record else None
