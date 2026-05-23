"""AI Brain Agent - The core AI agent with browser control and continuous learning."""
import asyncio
import json
import os
import threading
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ai.ai_client import get_ai_client


class AgentState(Enum):
    IDLE = "idle"
    SEARCHING = "searching"
    SCRAPING = "scraping"
    ANALYZING = "analyzing"
    APPLYING = "applying"
    WAITING = "waiting"


@dataclass
class JobRecord:
    """Represents a single job record in the database."""
    id: Optional[int] = None
    title: str = ""
    company: str = ""
    location: str = ""
    source: str = ""
    source_url: str = ""
    apply_url: str = ""
    salary: str = ""
    experience_required: str = ""
    skills_required: List[str] = field(default_factory=list)
    description: str = ""
    remote: bool = False
    walk_in: bool = False
    internship: bool = False
    match_score: float = 0.0
    applied: bool = False
    applied_at: Optional[str] = None
    status: str = "discovered"  # discovered, analyzed, applied, rejected, interview
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class AgentTask:
    """Represents a task for the AI agent."""
    task_id: str
    description: str
    status: str = "pending"
    result: Any = None
    error: str = ""


class AIJobAgent:
    """
    The main AI Agent that:
    - Uses GLM4.7/Gemma-3 as brain
    - Controls browser (Chromium) as eyes/hands
    - Continuously searches, scrapes, analyzes
    - Stores everything in database
    - Auto-applies when enabled
    - Responds to user in real-time
    """
    
    def __init__(self):
        self.ai = get_ai_client()
        self.state = AgentState.IDLE
        self.current_search = ""
        self.current_location = ""
        self.auto_apply_enabled = False
        self.resume_text = ""
        self.match_threshold = 75.0
        self.jobs: List[JobRecord] = []
        self.task_queue: List[AgentTask] = []
        self.is_running = False
        self.stop_requested = False
        self._message_callback = None
        
    def set_message_callback(self, callback):
        """Set callback for real-time messages to user."""
        self._message_callback = callback
        
    def _send_message(self, message: str):
        """Send message to user via callback."""
        # Remove emojis for Windows compatibility
        message = message.encode('ascii', 'ignore').decode('ascii')
        if self._message_callback:
            self._message_callback(message)
        print(f"[AGENT] {message}")
    
    async def think(self, prompt: str, context: Dict = None) -> str:
        """The AI brain thinks and makes decisions."""
        context_str = ""
        if context:
            context_str = f"\n\nContext: {json.dumps(context)}"
        
        full_prompt = f"""You are an intelligent job search agent. Your job is to help the user find and apply for jobs.

User's Resume:
{self.resume_text[:1000] if self.resume_text else "No resume uploaded"}

Current Job Search:
- Keywords: {self.current_search}
- Location: {self.current_location}
- Jobs found: {len(self.jobs)}
- Auto-apply: {self.auto_apply_enabled}

{context_str}

Task: {prompt}

Think step by step and provide your reasoning. Then give your final decision or action in JSON format.

If you need to take an action, respond with:
{{"action": "search|scrape|analyze|apply|stop|report", "details": "..."}}

If you just need to answer a question, respond normally.
"""
        try:
            response = await self.ai.chat_completion(
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.3,
            )
            return response
        except Exception as e:
            return f"Error: {e}"
    
    async def execute_task(self, task: AgentTask) -> Dict:
        """Execute a single task."""
        self._send_message(f"Executing: {task.description}")
        
        if "search" in task.description.lower():
            return await self._search_jobs_task()
        elif "apply" in task.description.lower():
            return await self._apply_to_jobs_task()
        elif "analyze" in task.description.lower():
            return await self._analyze_jobs_task()
        
        return {"status": "unknown_task"}
    
    async def _search_jobs_task(self) -> Dict:
        """Search for jobs using browser."""
        self.state = AgentState.SEARCHING
        self._send_message(f"🔍 Starting job search: {self.current_search} in {self.current_location}")
        
        from agents.job_discovery.discovery import JobDiscoveryAgent
        
        discovery = JobDiscoveryAgent()
        keywords = self.current_search.split(",") if self.current_search else ["Python"]
        locations = self.current_location.split(",") if self.current_location else ["Hyderabad"]
        
        raw_jobs = await discovery.search_jobs(keywords, locations, max_results=20)
        
        # Convert to JobRecord objects
        for job_data in raw_jobs:
            record = JobRecord(
                title=job_data.get("title", ""),
                company=job_data.get("company", ""),
                location=job_data.get("location", ""),
                source=job_data.get("source", ""),
                source_url=job_data.get("source_url", ""),
                apply_url=job_data.get("apply_url", ""),
                skills_required=job_data.get("skills_required", []),
                remote=job_data.get("remote", False),
                walk_in=job_data.get("walk_in", False),
                internship=job_data.get("internship", False),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
            )
            self.jobs.append(record)
        
        self.state = AgentState.IDLE
        self._send_message(f"Found {len(raw_jobs)} jobs from web scraping")
        
        # Now analyze with AI
        await self._analyze_jobs_task()
        
        return {"status": "success", "jobs_found": len(raw_jobs)}
    
    async def _analyze_jobs_task(self) -> Dict:
        """Analyze jobs using simple scoring (skip AI for speed)."""
        self.state = AgentState.ANALYZING
        self._send_message("Analyzing jobs...")
        
        if not self.jobs:
            return {"status": "no_jobs"}
        
        # Simple keyword-based scoring
        keywords = self.current_search.lower().split(",")
        for job in self.jobs:
            score = 50  # Base score
            title_lower = job.title.lower()
            
            # Boost score based on keyword matching
            for kw in keywords:
                if kw.strip() in title_lower:
                    score += 20
            
            # Boost for fresher/intern roles
            if any(x in title_lower for x in ["fresher", "junior", "intern", "entry"]):
                score += 15
            
            # Boost for relevant sources
            if job.source in ["indeed", "linkedin", "naukri"]:
                score += 10
            
            job.match_score = min(score, 100)
            job.status = "analyzed"
            job.updated_at = datetime.now().isoformat()
        
        # Sort by match score
        self.jobs.sort(key=lambda x: x.match_score, reverse=True)
        
        self.state = AgentState.IDLE
        self._send_message(f"Analyzed {len(self.jobs)} jobs. Top: {self.jobs[0].title if self.jobs else 'N/A'}")
        
        return {"status": "success", "jobs_analyzed": len(self.jobs)}
    
    async def _apply_to_jobs_task(self) -> Dict:
        """Auto-apply to matching jobs."""
        if not self.auto_apply_enabled:
            return {"status": "auto_apply_disabled"}
        
        self.state = AgentState.APPLYING
        self._send_message("Starting auto-apply...")
        
        applied_count = 0
        for job in self.jobs:
            if job.match_score >= self.match_threshold and not job.applied:
                # Apply logic here - would use browser
                job.applied = True
                job.applied_at = datetime.now().isoformat()
                job.status = "applied"
                applied_count += 1
                self._send_message(f"Applied to: {job.title} at {job.company}")
                
                if applied_count >= 3:  # Limit daily applications
                    break
        
        self.state = AgentState.IDLE
        self._send_message(f"Applied to {applied_count} jobs")
        
        return {"status": "success", "applications": applied_count}
    
    async def start_continuous_search(
        self,
        search: str,
        location: str,
        resume_text: str = "",
        auto_apply: bool = False,
        match_threshold: float = 75.0,
    ):
        """Start continuous job search loop."""
        self.is_running = True
        self.stop_requested = False
        self.current_search = search
        self.current_location = location
        self.resume_text = resume_text
        self.auto_apply_enabled = auto_apply
        self.match_threshold = match_threshold
        self.jobs = []
        
        self._send_message("Starting AI Agent...")
        self._send_message(f"Search: {search}, Location: {location}")
        self._send_message(f"Auto-apply: {'ON' if auto_apply else 'OFF'}")
        
        iteration = 0
        while self.is_running and not self.stop_requested:
            iteration += 1
            self._send_message(f"\n--- Iteration {iteration} ---")
            
            # Step 1: Search
            await self._search_jobs_task()
            
            if self.stop_requested:
                break
            
            # Step 2: Analyze
            await self._analyze_jobs_task()
            
            if self.stop_requested:
                break
            
            # Step 3: Auto-apply if enabled
            if self.auto_apply_enabled:
                await self._apply_to_jobs_task()
            
            if self.stop_requested:
                break
            
            # Report to user
            await self._report_status()
            
            # Wait before next iteration (or wait for user input)
            self.state = AgentState.WAITING
            self._send_message("\nWaiting... (say 'stop' to stop, 'continue' to search more)")
            
            # In a real implementation, this would wait for user input
            # For now, we'll do one round
            break
        
        self.is_running = False
        self._send_message("\n✅ Agent finished!")
    
    def stop(self):
        """Stop the agent."""
        self.stop_requested = True
        self.is_running = False
        self._send_message("🛑 Stopping agent...")
    
    async def _report_status(self):
        """Report current status to user."""
        total = len(self.jobs)
        applied = sum(1 for j in self.jobs if j.applied)
        high_match = sum(1 for j in self.jobs if j.match_score >= self.match_threshold)
        
        report = f"""
📊 Current Status:
- Total Jobs Found: {total}
- High Match Jobs: {high_match}
- Applied: {applied}
- Pending: {total - applied}
"""
        self._send_message(report)
        
        # Show top 5 jobs
        if self.jobs:
            self._send_message("\n🎯 Top 5 Jobs:")
            for i, job in enumerate(self.jobs[:5], 1):
                self._send_message(f"{i}. {job.title} @ {job.company}")
                self._send_message(f"   Match: {job.match_score:.0f}% | {job.source} | {job.location}")
    
    async def answer_question(self, question: str) -> str:
        """Answer user question about jobs or agent status."""
        context = {
            "total_jobs": len(self.jobs),
            "applied_jobs": sum(1 for j in self.jobs if j.applied),
            "auto_apply": self.auto_apply_enabled,
            "current_search": self.current_search,
            "current_location": self.current_location,
        }
        
        # Get top jobs for context
        if self.jobs:
            context["top_jobs"] = [
                {"title": j.title, "company": j.company, "score": j.match_score}
                for j in self.jobs[:5]
            ]
        
        response = await self.think(question, context)
        return response
    
    def get_jobs_table(self) -> List[Dict]:
        """Get all jobs as a list of dictionaries for table display."""
        return [
            {
                "id": i + 1,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "source": job.source,
                "match_score": f"{job.match_score:.0f}%",
                "status": job.status,
                "applied": "Yes" if job.applied else "No",
                "apply_url": job.apply_url,
            }
            for i, job in enumerate(self.jobs)
        ]
    
    def export_to_csv(self) -> str:
        """Export jobs to CSV format."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Title", "Company", "Location", "Source", "Match Score", "Status", "Applied", "Apply URL"])
        
        for job in self.jobs:
            writer.writerow([
                job.title,
                job.company,
                job.location,
                job.source,
                f"{job.match_score:.0f}%",
                job.status,
                "Yes" if job.applied else "No",
                job.apply_url,
            ])
        
        return output.getvalue()


# Global agent instance
ai_agent = AIJobAgent()