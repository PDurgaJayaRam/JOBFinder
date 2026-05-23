"""Multi-Agent Workflow System - Different agents for different tasks."""
import asyncio
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ai.ai_client import get_ai_client
from agents.job_discovery.discovery import JobDiscoveryAgent
from scrapers.firecrawl_client import JobScraperAgent


class TaskType(Enum):
    SEARCH = "search"
    SCRAPE = "scrape"
    ANALYZE = "analyze"
    APPLY = "apply"
    OUTREACH = "outreach"
    REPORT = "report"


@dataclass
class AgentTask:
    """Task assigned to an agent."""
    task_id: str
    task_type: TaskType
    description: str
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None
    error: str = ""
    created_at: str = ""
    completed_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class SearchAgent:
    """Agent responsible for finding jobs."""
    
    def __init__(self):
        self.scraper = JobScraperAgent()
    
    async def execute(self, keywords: List[str], location: str, max_results: int = 20) -> List[Dict]:
        """Execute search task."""
        jobs = await self.scraper.search_jobs(keywords, [location], max_results)
        return jobs


class ScrapeAgent:
    """Agent responsible for scraping detailed job info."""
    
    def __init__(self):
        pass
    
    async def execute(self, job_url: str) -> Dict:
        """Scrape detailed job information."""
        from bs4 import BeautifulSoup
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(job_url)
                soup = BeautifulSoup(resp.text, "lxml")
                
                # Extract description
                desc_elem = soup.find("div", {"id": "jobDescriptionText"}) or soup.find("div", class_="description")
                description = desc_elem.get_text(strip=True) if desc_elem else ""
                
                return {
                    "success": True,
                    "description": description[:2000],
                    "url": job_url
                }
        except Exception as e:
            return {"success": False, "error": str(e)}


class AnalyzeAgent:
    """Agent responsible for analyzing and scoring jobs using NVIDIA AI."""
    
    def __init__(self):
        self.ai = get_ai_client()
    
    async def execute(self, job: Dict, resume_text: str = "") -> Dict:
        """Analyze job and calculate match score using AI."""
        title = job.get("title", "")
        company = job.get("company", "")
        description = job.get("description", "")[:2000]

        try:
            prompt = f"""You are a job matching assistant. Analyze this job for a candidate.

Job Title: {title}
Company: {company}
Description: {description[:500]}

Resume (if provided): {resume_text[:500] if resume_text else "No resume provided"}

Provide a JSON response with:
- match_score (0-100): How well this job matches
- match_reason: Why it's a good/bad fit
- key_skills: List of skills mentioned
- recommendation: "apply" or "skip" or "maybe"

Format: {{"match_score": 75, "match_reason": "...", "key_skills": ["Python", "SQL"], "recommendation": "apply"}}"""

            result = await self.ai.chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert job matching AI. Analyze jobs and provide scores."},
                    {"role": "user", "content": prompt}
                ],
                model="mistralai/mistral-large-3-675b-instruct-2512",
                temperature=0.3,
                max_tokens=500,
                json_mode=True
            )

            import json
            import re
            # Parse JSON from response
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                data = json.loads(json_match.group())
                job["match_score"] = data.get("match_score", 50)
                job["match_reason"] = data.get("match_reason", "")
                job["ai_skills"] = data.get("key_skills", [])
                job["ai_recommendation"] = data.get("recommendation", "maybe")
            else:
                job["match_score"] = 50
                job["match_reason"] = "AI analysis incomplete"
        except Exception as e:
            print(f"AI analysis error: {e}", flush=True)
            # Fallback to simple scoring
            score = 50
            title_lower = title.lower()
            resume_lower = resume_text.lower() if resume_text else ""
            keywords = ["python", "data", "analyst", "developer", "engineer", "sql", "ai", "ml"]
            for kw in keywords:
                if kw in title_lower:
                    score += 15
                if kw in resume_lower:
                    score += 10
            if any(x in title_lower for x in ["fresher", "junior", "intern", "entry"]):
                score += 20
            if "remote" in title_lower:
                score += 10
            if job.get("walk_in"):
                score += 15
            job["match_score"] = min(score, 100)
            job["match_reason"] = f"Fallback scoring (AI failed: {str(e)[:50]})"

        job["status"] = "analyzed"
        return job


class ApplyAgent:
    """Agent responsible for applying to jobs."""
    
    def __init__(self):
        pass
    
    async def execute(self, job: Dict, resume_text: str = "") -> Dict:
        """Apply to a job using browser automation."""
        apply_url = job.get("apply_url")
        
        if not apply_url:
            return {"success": False, "error": "No apply URL"}
        
        # In a full implementation, this would:
        # 1. Open browser
        # 2. Navigate to apply URL
        # 3. Fill form fields
        # 4. Upload resume
        # 5. Submit
        
        # For now, mark as "would apply"
        return {
            "success": True,
            "job_title": job.get("title"),
            "applied_at": datetime.now().isoformat(),
            "note": f"Would apply to {apply_url}"
        }


class OutreachAgent:
    """Agent responsible for finding contacts and generating outreach."""
    
    def __init__(self):
        self.ai = get_ai_client()
    
    async def execute(self, company: str, job_title: str = "") -> Dict:
        """Find contacts and generate outreach message."""
        # Would use LinkedIn scraping, company website parsing, etc.
        return {
            "company": company,
            "contacts": [],
            "outreach_message": f"Hi, I'm interested in the {job_title} position at {company}."
        }


class ReportAgent:
    """Agent responsible for generating reports."""
    
    def __init__(self):
        pass
    
    async def execute(self, jobs: List[Dict], stats: Dict = None) -> Dict:
        """Generate a job search report."""
        
        total = len(jobs)
        applied = sum(1 for j in jobs if j.get("applied"))
        high_match = sum(1 for j in jobs if j.get("match_score", 0) >= 75)
        remote = sum(1 for j in jobs if j.get("remote"))
        walk_in = sum(1 for j in jobs if j.get("walk_in"))
        
        # Count by source
        sources = {}
        for job in jobs:
            src = job.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1
        
        return {
            "total_jobs": total,
            "applied": applied,
            "pending": total - applied,
            "high_match": high_match,
            "remote_jobs": remote,
            "walk_in_jobs": walk_in,
            "by_source": sources,
            "generated_at": datetime.now().isoformat()
        }


class MultiAgentWorkflow:
    """
    Coordinates multiple agents for complete job search workflow.
    Each agent has a specific role.
    """
    
    def __init__(self):
        self.search_agent = SearchAgent()
        self.scrape_agent = ScrapeAgent()
        self.analyze_agent = AnalyzeAgent()
        self.apply_agent = ApplyAgent()
        self.outreach_agent = OutreachAgent()
        self.report_agent = ReportAgent()
        
        self.jobs: List[Dict] = []
        self.tasks: List[AgentTask] = []
        self.is_running = False
        self.progress = 0
    
    async def run_full_workflow(
        self,
        keywords: List[str],
        location: str,
        resume_text: str = "",
        auto_apply: bool = False,
        match_threshold: float = 75.0,
        max_results: int = 20,
    ) -> Dict:
        """Run the complete multi-agent workflow."""
        
        self.is_running = True
        self.jobs = []
        self.progress = 0
        
        workflow_log = []
        
        # Phase 1: Search (Search Agent)
        workflow_log.append({"phase": "search", "status": "started", "message": "Searching for jobs..."})
        jobs = await self.search_agent.execute(keywords, location, max_results)
        self.jobs = jobs
        self.progress = 20
        workflow_log.append({"phase": "search", "status": "completed", "message": f"Found {len(jobs)} jobs"})
        
        # Phase 2: Analyze (Analyze Agent)
        workflow_log.append({"phase": "analyze", "status": "started", "message": "Analyzing and scoring jobs..."})
        for job in self.jobs:
            job = await self.analyze_agent.execute(job, resume_text)
        self.progress = 50
        workflow_log.append({"phase": "analyze", "status": "completed", "message": "Analysis complete"})
        
        # Sort by match score
        self.jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        # Phase 3: Apply (Apply Agent) - if enabled
        if auto_apply:
            workflow_log.append({"phase": "apply", "status": "started", "message": "Applying to matching jobs..."})
            applied_count = 0
            for job in self.jobs:
                if job.get("match_score", 0) >= match_threshold and not job.get("applied"):
                    result = await self.apply_agent.execute(job, resume_text)
                    if result.get("success"):
                        job["applied"] = True
                        job["applied_at"] = result.get("applied_at")
                        applied_count += 1
                        
                        if applied_count >= 5:  # Limit daily applications
                            break
            self.progress = 80
            workflow_log.append({"phase": "apply", "status": "completed", "message": f"Applied to {applied_count} jobs"})
        
        # Phase 4: Report (Report Agent)
        workflow_log.append({"phase": "report", "status": "started", "message": "Generating report..."})
        report = await self.report_agent.execute(self.jobs)
        self.progress = 100
        workflow_log.append({"phase": "report", "status": "completed", "message": "Report generated"})
        
        self.is_running = False
        
        return {
            "success": True,
            "workflow_log": workflow_log,
            "jobs": self.jobs,
            "report": report,
            "progress": self.progress
        }
    
    async def run_search_only(self, keywords: List[str], location: str, max_results: int = 20) -> Dict:
        """Run only search agent."""
        jobs = await self.search_agent.execute(keywords, location, max_results)
        self.jobs = jobs
        return {"jobs": jobs, "count": len(jobs)}
    
    async def run_analyze_only(self, resume_text: str = "") -> Dict:
        """Run only analyze agent on existing jobs."""
        for job in self.jobs:
            job = await self.analyze_agent.execute(job, resume_text)
        
        self.jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        return {"jobs": self.jobs, "count": len(self.jobs)}
    
    def get_jobs_table(self) -> List[Dict]:
        """Get jobs in table format."""
        return [
            {
                "id": i + 1,
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "source": job.get("source", ""),
                "match_score": f"{job.get('match_score', 0):.0f}%",
                "remote": "Yes" if job.get("remote") else "No",
                "walk_in": "Yes" if job.get("walk_in") else "No",
                "applied": "Yes" if job.get("applied") else "No",
                "apply_url": job.get("apply_url", ""),
            }
            for i, job in enumerate(self.jobs)
        ]
    
    def get_dashboard_summary(self) -> Dict:
        """Get dashboard summary with counts."""
        total = len(self.jobs)
        applied = sum(1 for j in self.jobs if j.get("applied"))
        pending = total - applied
        high_match = sum(1 for j in self.jobs if j.get("match_score", 0) >= 75)
        remote = sum(1 for j in self.jobs if j.get("remote"))
        walk_in = sum(1 for j in self.jobs if j.get("walk_in"))
        
        return {
            "total_jobs": total,
            "jobs_applied": applied,
            "jobs_pending": pending,
            "high_match": high_match,
            "remote_jobs": remote,
            "walk_in_jobs": walk_in,
            "progress": self.progress,
            "is_running": self.is_running
        }


# Global workflow instance
workflow = MultiAgentWorkflow()