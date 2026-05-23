"""Networking agent - generates outreach messages."""
from typing import Dict, Any
from ai.ai_client import get_ai_client
from ai.prompts import NETWORKING_PROMPT


class NetworkingAgent:
    """Generates personalized networking and outreach messages."""

    def __init__(self):
        self.ai = get_ai_client()

    async def generate_job_outreach(
        self,
        job: Dict[str, Any],
        resume_summary: str,
        recipient_name: str = "",
    ) -> str:
        """Generate a LinkedIn/recruiter outreach message for a specific job."""
        context = (
            f"Job: {job.get('title', '')} at {job.get('company', '')}\n"
            f"Location: {job.get('location', '')}\n"
            f"Candidate summary: {resume_summary}\n"
            f"Recipient: {recipient_name or 'Hiring Manager'}"
        )
        messages = [
            {"role": "system", "content": NETWORKING_PROMPT},
            {"role": "user", "content": context},
        ]
        return await self.ai.chat_completion(messages=messages, temperature=0.7, max_tokens=500)

    async def generate_referral_request(
        self,
        job: Dict[str, Any],
        resume_summary: str,
        contact_name: str = "",
    ) -> str:
        """Generate a polite referral request message."""
        context = (
            f"Request a referral for: {job.get('title', '')} at {job.get('company', '')}\n"
            f"Candidate summary: {resume_summary}\n"
            f"Contact: {contact_name or 'Colleague'}"
        )
        messages = [
            {"role": "system", "content": NETWORKING_PROMPT + "\nThis is a referral request. Be humble and clear."},
            {"role": "user", "content": context},
        ]
        return await self.ai.chat_completion(messages=messages, temperature=0.7, max_tokens=500)

    async def generate_lead_outreach(
        self,
        company: Dict[str, Any],
        contact: Dict[str, Any],
    ) -> str:
        """Generate a B2B lead outreach message (cold email style)."""
        context = (
            f"Company: {company.get('name', '')}\n"
            f"Pain signals: {', '.join(company.get('pain_signals', []))}\n"
            f"Automation ideas: {company.get('automation_ideas', [])}\n"
            f"Recipient: {contact.get('name', '')} ({contact.get('role', '')})"
        )
        messages = [
            {"role": "system", "content": NETWORKING_PROMPT + "\nThis is a B2B outreach offering automation help. Keep it professional and value-focused."},
            {"role": "user", "content": context},
        ]
        return await self.ai.chat_completion(messages=messages, temperature=0.7, max_tokens=500)
