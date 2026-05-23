"""Job intelligence agent - analyzes job descriptions with AI."""
import json
from typing import Dict, Any
from ai.ai_client import get_ai_client
from ai.prompts import JOB_ANALYSIS_PROMPT


class JobIntelligenceAgent:
    """Uses AI to analyze job descriptions and extract structured data."""

    def __init__(self):
        self.ai = get_ai_client()

    async def analyze_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a job listing using AI."""
        description = job.get("description", "")
        title = job.get("title", "")
        company = job.get("company", "")

        if not description:
            # Minimal fallback with new fields
            return {
                "role": title,
                "company": company,
                "experience_required": "",
                "required_skills": [],
                "preferred_skills": [],
                "location": job.get("location", ""),
                "salary_range": "",
                "remote": False,
                "hybrid": False,
                "walk_in": False,
                "internship": False,
                "fresher_friendly": "fresher" in title.lower() or "0-" in title.lower(),
                "job_type": "",
                "urgency": "medium",
                "summary": title,
                "red_flags": {"workload": [], "culture": [], "compensation": []},
            }

        messages = [
            {"role": "system", "content": JOB_ANALYSIS_PROMPT},
            {"role": "user", "content": f"Job Title: {title}\nCompany: {company}\n\nDescription:\n{description[:4000]}"},
        ]

        try:
            raw = await self.ai.chat_completion(messages=messages, temperature=0.2, json_mode=True)
            parsed = json.loads(raw)
            # Ensure red_flags field exists
            if "red_flags" not in parsed:
                parsed["red_flags"] = {"workload": [], "culture": [], "compensation": []}
            return parsed
        except Exception:
            # Fallback with new fields
            return {
                "role": title,
                "company": company,
                "experience_required": "",
                "required_skills": [],
                "preferred_skills": [],
                "location": job.get("location", ""),
                "salary_range": "",
                "remote": False,
                "hybrid": False,
                "walk_in": False,
                "internship": False,
                "fresher_friendly": False,
                "job_type": "",
                "urgency": "medium",
                "summary": description[:200],
                "red_flags": {"workload": [], "culture": [], "compensation": []},
            }
