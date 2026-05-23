"""Recruiter Intelligence - Combines people finding and company intelligence."""
from typing import Dict, Any, List, Optional
from agents.people_finder.finder import PeopleFinderAgent
from agents.company_intelligence.intel import CompanyIntelAgent
from agents.networking.messages import NetworkingAgent


class RecruiterIntelligence:
    """Orchestrates recruiter discovery, company analysis, and outreach generation."""

    def __init__(self):
        self.people_finder = PeopleFinderAgent()
        self.company_intel = CompanyIntelAgent()
        self.networking = NetworkingAgent()

    async def analyze_job_opportunity(self, job_data: Dict[str, Any], resume_summary: str = "") -> Dict[str, Any]:
        """Full analysis of a job opportunity: company intel + recruiter finding + outreach draft."""
        company_name = job_data.get("company", "")
        if not company_name:
            return {"error": "No company name in job data"}

        company_intel = await self.company_intel.analyze_job_company(job_data)

        recruiters = await self.people_finder.find_recruiters_for_job(job_data)

        outreach_draft = ""
        if recruiters and resume_summary:
            top_recruiter = recruiters[0]
            outreach_draft = await self.networking.generate_job_outreach(
                job=job_data,
                resume_summary=resume_summary,
                recipient_name=top_recruiter.get("name", ""),
            )

        return {
            "company_name": company_name,
            "company_intelligence": company_intel,
            "recruiters_found": len(recruiters),
            "recruiters": recruiters[:5],
            "outreach_draft": outreach_draft,
            "is_actively_hiring": company_intel.get("is_actively_hiring", False),
            "hiring_signals": company_intel.get("hiring_signals", []),
            "tech_stack": company_intel.get("tech_stack", []),
            "company_priority": company_intel.get("priority", "cold"),
        }

    async def find_contacts_for_company(
        self,
        company_name: str,
        website: str = "",
        role_hint: str = "recruiter",
    ) -> List[Dict[str, Any]]:
        """Find contacts for a specific company."""
        all_contacts = []

        linkedin_results = await self.people_finder.search_linkedin_public(company_name, role_hint)
        all_contacts.extend(linkedin_results)

        if website:
            team_results = await self.people_finder.scrape_company_team_page(website)
            all_contacts.extend(team_results)

        for contact in all_contacts:
            if not contact.get("email"):
                contact["email"] = await self.people_finder.find_email_by_pattern(
                    company_name, contact["name"], website
                )

        seen = set()
        unique = []
        for c in all_contacts:
            key = c.get("name", "") + c.get("linkedin_url", "")
            if key not in seen:
                seen.add(key)
                unique.append(c)

        return unique

    async def generate_outreach(
        self,
        job: Dict[str, Any],
        recruiter: Dict[str, Any],
        resume_summary: str,
        message_type: str = "email",
    ) -> str:
        """Generate personalized outreach message to a recruiter."""
        if message_type == "referral":
            return await self.networking.generate_referral_request(
                job=job,
                resume_summary=resume_summary,
                contact_name=recruiter.get("name", ""),
            )
        return await self.networking.generate_job_outreach(
            job=job,
            resume_summary=resume_summary,
            recipient_name=recruiter.get("name", ""),
        )
