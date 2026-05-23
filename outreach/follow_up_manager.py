"""Follow-up automation logic."""
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from outreach.email_sender import EmailSender, EmailResult
from outreach.email_tracker import EmailTracker, EmailRecord
from agents.networking.messages import NetworkingAgent

logger = logging.getLogger(__name__)

FOLLOW_UP_SCHEDULE = [
    {"days_after": 3, "template": "gentle_reminder"},
    {"days_after": 7, "template": "value_add"},
    {"days_after": 14, "template": "final_followup"},
]


class FollowUpManager:
    """Manages follow-up email sequences."""

    def __init__(
        self,
        email_sender: EmailSender,
        email_tracker: EmailTracker,
        networking_agent: Optional[NetworkingAgent] = None,
    ):
        self.email_sender = email_sender
        self.email_tracker = email_tracker
        self.networking = networking_agent or NetworkingAgent()

    async def generate_follow_up(
        self,
        original_email: EmailRecord,
        job: Dict[str, Any],
        resume_summary: str,
        template: str = "gentle_reminder",
    ) -> str:
        """Generate a follow-up message."""
        templates = {
            "gentle_reminder": (
                f"Hi {job.get('recipient_name', 'there')},\n\n"
                f"I wanted to follow up on my previous email regarding the {job.get('title', '')} position at {job.get('company', '')}.\n\n"
                f"I remain very interested in this opportunity and would love to discuss how my background in {resume_summary[:100]} could benefit your team.\n\n"
                f"Best regards"
            ),
            "value_add": (
                f"Hi {job.get('recipient_name', 'there')},\n\n"
                f"Following up on my application for the {job.get('title', '')} role at {job.get('company', '')}.\n\n"
                f"Since my last email, I've been thinking more about how my experience could contribute to {job.get('company', '')}'s goals. "
                f"I'd welcome the opportunity to discuss this further.\n\n"
                f"Best regards"
            ),
            "final_followup": (
                f"Hi {job.get('recipient_name', 'there')},\n\n"
                f"This is my final follow-up regarding the {job.get('title', '')} position.\n\n"
                f"I understand you may be busy with the hiring process. If the role has been filled, I'd appreciate a brief confirmation. "
                f"Otherwise, I remain very interested and available to discuss.\n\n"
                f"Thank you for your time.\n\n"
                f"Best regards"
            ),
        }

        return templates.get(template, templates["gentle_reminder"])

    def should_follow_up(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Check if an email needs a follow-up. Returns follow-up config if yes."""
        record = self.email_tracker.get_record(email_id)
        if not record:
            return None

        if record.status in ["replied", "bounced"]:
            return None

        if record.status != "sent" or not record.sent_at:
            return None

        sent_time = datetime.fromisoformat(record.sent_at)
        now = datetime.utcnow()
        days_since_sent = (now - sent_time).days

        next_follow_up_index = record.follow_up_count
        if next_follow_up_index >= len(FOLLOW_UP_SCHEDULE):
            return None

        schedule = FOLLOW_UP_SCHEDULE[next_follow_up_index]
        if days_since_sent >= schedule["days_after"]:
            return schedule

        return None

    async def send_follow_up(
        self,
        email_id: str,
        job: Dict[str, Any],
        resume_summary: str,
        from_name: str = "",
    ) -> EmailResult:
        """Send a follow-up email."""
        record = self.email_tracker.get_record(email_id)
        if not record:
            return EmailResult(success=False, error="Email record not found")

        schedule = self.should_follow_up(email_id)
        if not schedule:
            return EmailResult(success=False, error="Not yet time for follow-up")

        follow_up_body = await self.generate_follow_up(
            original_email=record,
            job=job,
            resume_summary=resume_summary,
            template=schedule["template"],
        )

        subject = f"Re: {record.subject}"
        follow_up_id = f"fu_{email_id}_{record.follow_up_count + 1}"

        self.email_tracker.create_record(
            email_id=follow_up_id,
            to_email=record.to_email,
            subject=subject,
            body=follow_up_body,
            job_id=record.job_id,
            recruiter_id=record.recruiter_id,
            message_type="follow_up",
            metadata={"original_email_id": email_id},
        )

        result = self.email_sender.send_email(
            to_email=record.to_email,
            subject=subject,
            body=follow_up_body,
            from_name=from_name,
        )

        if result.success:
            self.email_tracker.mark_sent(follow_up_id, result.message_id)
            self.email_tracker.record_follow_up(email_id)
            logger.info(f"Follow-up sent for {email_id}: {follow_up_id}")
        else:
            logger.error(f"Follow-up failed for {email_id}: {result.error}")

        return result

    async def process_all_follow_ups(
        self,
        jobs_data: Dict[int, Dict[str, Any]],
        resume_summary: str,
        from_name: str = "",
    ) -> List[Dict[str, Any]]:
        """Process follow-ups for all eligible emails."""
        results = []
        sent_emails = self.email_tracker.get_records_by_status("sent")

        for record in sent_emails:
            if record.message_type == "follow_up":
                continue

            schedule = self.should_follow_up(record.id)
            if schedule:
                job_data = jobs_data.get(record.job_id, {})
                result = await self.send_follow_up(
                    email_id=record.id,
                    job=job_data,
                    resume_summary=resume_summary,
                    from_name=from_name,
                )
                results.append({
                    "email_id": record.id,
                    "follow_up_id": f"fu_{record.id}_{record.follow_up_count + 1}",
                    "success": result.success,
                    "error": result.error,
                })

        return results
