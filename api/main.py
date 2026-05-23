"""FastAPI main application with all routes."""
import os
import sys
import asyncio

# Windows fix: Force ProactorEventLoop BEFORE any event loop is created
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import csv
import io
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from pydantic import BaseModel

from database.engine import init_db
import database.models  # Import to register models with Base
from agents.orchestrator.orchestrator import AgentOrchestrator
from agents.tracking.tracker import TrackingAgent
from agents.vision_scraper.models import NavigationStatus


class SearchRequest(BaseModel):
    resume_text: str = ""
    keywords: List[str] = ["Python", "Data Analyst"]
    locations: List[str] = ["Hyderabad"]
    auto_apply: bool = False
    match_threshold: float = 75.0
    max_jobs: int = 20


class LeadRequest(BaseModel):
    companies: List[Dict[str, Any]]
    target_niche: Optional[str] = None


class ComboRequest(BaseModel):
    resume_text: str = ""
    keywords: List[str] = ["Python"]
    locations: List[str] = ["Hyderabad"]
    companies: Optional[List[Dict[str, Any]]] = None
    auto_apply: bool = False
    match_threshold: float = 75.0


orchestrator = AgentOrchestrator()
tracker = TrackingAgent()

# AI Agent for continuous search
from agents.ai_brain.agent import ai_agent
from agents.workflow.multi_agent import workflow

# Store for messages
agent_messages = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Combo AI Agent",
    description="Autonomous Career Agent + Lead Generation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    chat_path = project_root / "frontend" / "public" / "chat.html"
    if chat_path.exists():
        return FileResponse(str(chat_path))
    dashboard_path = project_root / "frontend" / "public" / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path))
    return {"status": "ok", "app": "Job AI Agent", "version": "1.0.0"}


@app.get("/dashboard")
async def dashboard():
    dashboard_path = project_root / "frontend" / "public" / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path))
    return {"status": "ok", "message": "Dashboard not found"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/jobs/search")
async def search_jobs(req: SearchRequest):
    """Run job discovery + intelligence + resume matching pipeline."""
    try:
        result = await orchestrator.run_job_pipeline(
            resume_text=req.resume_text,
            keywords=req.keywords,
            locations=req.locations,
            auto_apply=req.auto_apply,
            match_threshold=req.match_threshold,
            max_jobs=req.max_jobs,
        )
        return {
            "success": True,
            "jobs_discovered": result.jobs_discovered,
            "jobs_matched": result.jobs_matched,
            "applications_submitted": result.applications_submitted,
            "errors": result.errors,
            "jobs": result.jobs,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/jobs/export/csv")
async def export_jobs_csv(req: SearchRequest):
    """Export job listings as CSV file."""
    try:
        result = await orchestrator.run_job_pipeline(
            resume_text=req.resume_text,
            keywords=req.keywords,
            locations=req.locations,
            auto_apply=False,
            match_threshold=0,
            max_jobs=req.max_jobs,
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Title", "Company", "Location", "Source", "Match Score",
            "Skills", "Experience Required", "Salary Range",
            "Remote", "Internship", "Summary", "Job URL"
        ])

        for job in result.jobs:
            writer.writerow([
                job.get("title", ""),
                job.get("company", ""),
                job.get("location", ""),
                job.get("source", ""),
                f"{job.get('match_score', 0):.1f}%",
                ", ".join(job.get("skills", [])),
                job.get("experience_required", ""),
                job.get("salary_range", ""),
                job.get("remote", False),
                job.get("internship", False),
                job.get("summary", "")[:200],
                job.get("source_url", ""),
            ])

        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=jobs_export.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/leads/enrich")
async def enrich_leads(req: LeadRequest):
    """Run lead enrichment and outreach generation pipeline."""
    try:
        result = await orchestrator.run_lead_pipeline(
            companies=req.companies,
            target_niche=req.target_niche,
        )
        return {
            "success": True,
            "leads_generated": result.leads_generated,
            "messages_generated": result.messages_generated,
            "errors": result.errors,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/combo/run")
async def run_combo(req: ComboRequest):
    """Run both job pipeline and lead pipeline in parallel."""
    try:
        result = await orchestrator.run_full_combo(
            resume_text=req.resume_text,
            keywords=req.keywords,
            locations=req.locations,
            companies=req.companies,
            auto_apply=req.auto_apply,
            match_threshold=req.match_threshold,
        )
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/applications")
async def get_applications(status: Optional[str] = Query(None)):
    apps = await tracker.get_applications(status=status)
    return {"applications": apps}


@app.get("/analytics/outreach")
async def get_outreach():
    outreach = await tracker.get_outreach()
    return {"outreach": outreach}


@app.get("/analytics/dashboard")
async def get_dashboard():
    return await tracker.get_analytics()


@app.post("/resume/parse")
async def parse_resume(file: UploadFile = File(...)):
    """Accept a resume file and extract text from PDF, DOCX, or TXT."""
    try:
        content = await file.read()
        filename = file.filename.lower()
        text = ""

        if filename.endswith(".pdf"):
            from pypdf import PdfReader
            from io import BytesIO
            reader = PdfReader(BytesIO(content))
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        elif filename.endswith(".docx"):
            from docx import Document
            from io import BytesIO
            doc = Document(BytesIO(content))
            for para in doc.paragraphs:
                text += para.text + "\n"

        elif filename.endswith(".txt"):
            text = content.decode("utf-8", errors="ignore")

        else:
            # Try as plain text fallback
            text = content.decode("utf-8", errors="ignore")

        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from file. Try .txt format.")

        return {"filename": file.filename, "extracted_text": text.strip()[:5000]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse resume: {e}")


# === AI AGENT CONTROLS ===

class AgentStartRequest(BaseModel):
    search: str = "Python"
    location: str = "Hyderabad"
    resume_text: str = ""
    auto_apply: bool = False
    match_threshold: float = 75.0


class AgentQuestionRequest(BaseModel):
    question: str


@app.post("/agent/start")
async def start_agent(req: AgentStartRequest):
    """Start the AI agent for continuous job search."""
    try:
        # Set message callback to collect messages
        messages = []
        def msg_callback(msg):
            messages.append({"message": msg, "time": datetime.now().isoformat()})
        
        ai_agent.set_message_callback(msg_callback)
        
        # Start the agent in background
        asyncio.create_task(
            ai_agent.start_continuous_search(
                search=req.search,
                location=req.location,
                resume_text=req.resume_text,
                auto_apply=req.auto_apply,
                match_threshold=req.match_threshold,
            )
        )
        
        return {
            "status": "started",
            "message": f"AI Agent started searching for '{req.search}' in {req.location}",
            "messages": messages,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/stop")
async def stop_agent():
    """Stop the AI agent."""
    ai_agent.stop()
    return {"status": "stopped", "message": "AI Agent stopped"}


@app.get("/agent/status")
async def get_agent_status():
    """Get current agent status."""
    return {
        "is_running": ai_agent.is_running,
        "state": ai_agent.state.value,
        "search": ai_agent.current_search,
        "location": ai_agent.current_location,
        "auto_apply": ai_agent.auto_apply_enabled,
        "total_jobs": len(ai_agent.jobs),
        "jobs_table": ai_agent.get_jobs_table(),
    }


@app.get("/agent/jobs")
async def get_agent_jobs():
    """Get all jobs found by agent in table format."""
    return {
        "jobs": ai_agent.get_jobs_table(),
        "total": len(ai_agent.jobs),
        "export_csv": ai_agent.export_to_csv(),
    }


@app.post("/agent/question")
async def ask_agent(req: AgentQuestionRequest):
    """Ask the AI agent a question."""
    try:
        answer = await ai_agent.answer_question(req.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/messages")
async def get_agent_messages():
    """Get all messages from agent."""
    return {"messages": agent_messages}


@app.post("/agent/auto-apply/toggle")
async def toggle_auto_apply(enabled: bool = True):
    """Toggle auto-apply on/off."""
    ai_agent.auto_apply_enabled = enabled
    return {"auto_apply": enabled, "message": f"Auto-apply {'enabled' if enabled else 'disabled'}"}


# === MULTI-AGENT WORKFLOW ENDPOINTS ===

class WorkflowRequest(BaseModel):
    keywords: List[str] = ["Python", "Data Analyst"]
    location: str = "Hyderabad"
    resume_text: str = ""
    auto_apply: bool = False
    match_threshold: float = 75.0
    max_results: int = 20


@app.post("/workflow/run")
async def run_workflow(req: WorkflowRequest):
    """Run complete multi-agent workflow: search -> analyze -> apply -> report."""
    try:
        result = await workflow.run_full_workflow(
            keywords=req.keywords,
            location=req.location,
            resume_text=req.resume_text,
            auto_apply=req.auto_apply,
            match_threshold=req.match_threshold,
            max_results=req.max_results,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workflow/search")
async def workflow_search(req: WorkflowRequest):
    """Run search only with multi-agent."""
    try:
        result = await workflow.run_search_only(
            keywords=req.keywords,
            location=req.location,
            max_results=req.max_results,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/dashboard")
async def workflow_dashboard():
    """Get dashboard summary with job counts."""
    return workflow.get_dashboard_summary()


@app.get("/workflow/jobs")
async def workflow_jobs():
    """Get all jobs in table format."""
    return {
        "jobs": workflow.get_jobs_table(),
        "count": len(workflow.jobs)
    }


@app.get("/workflow/progress")
async def workflow_progress():
    """Get current workflow progress."""
    return {
        "progress": workflow.progress,
        "is_running": workflow.is_running,
        "total_jobs": len(workflow.jobs)
    }


@app.post("/workflow/analyze")
async def workflow_analyze(resume_text: str = ""):
    """Analyze existing jobs."""
    try:
        result = await workflow.run_analyze_only(resume_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === CHAT INTERFACE ===

class ChatRequest(BaseModel):
    user_id: str = ""
    message: str
    resume_text: str = ""
    keywords: str = "Python"
    location: str = "Hyderabad"
    target_count: int = 20
    experience: str = "fresher"
    portals: List[str] = []
    history: List[Dict[str, str]] = []
    jobs: List[Dict[str, Any]] = []


chat_agent_instance = None


@app.post("/chat")
async def chat(req: ChatRequest):
    """Chat with the AI agent."""
    global chat_agent_instance
    if chat_agent_instance is None:
        from agents.chat_agent.agent import ChatAgent
        chat_agent_instance = ChatAgent()

    context = {
        "user_id": req.user_id or "default_user",
        "resume_text": req.resume_text,
        "keywords": req.keywords,
        "location": req.location,
        "target_count": req.target_count,
        "experience": req.experience,
        "portals": req.portals,
        "history": req.history[-10:],
        "jobs": req.jobs,
    }

    try:
        result = await chat_agent_instance.route_message(req.message, context)
        return result
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Chat error: {error_detail}", flush=True)
        return {
            "response": f"Error: {str(e)}",
            "tool_uses": chat_agent_instance.get_tool_log(),
            "jobs": []
        }


# === SAVED JOBS DASHBOARD ===

@app.get("/saved-jobs")
async def get_saved_jobs(limit: int = 100, offset: int = 0, status: str = None):
    """Get all saved jobs from database."""
    from agents.job_saver import JobSaver
    saver = JobSaver()
    jobs = await saver.get_all_jobs(limit=limit, offset=offset, status=status)
    return {"jobs": jobs, "count": len(jobs)}


@app.get("/saved-jobs/stats")
async def get_saved_jobs_stats():
    """Get saved jobs statistics."""
    from agents.job_saver import JobSaver
    saver = JobSaver()
    return await saver.get_stats()


@app.post("/saved-jobs/apply/{job_id}")
async def apply_to_saved_job(job_id: int):
    """Mark a job as applied."""
    from database.engine import async_session
    from database.models import Job, JobStatus
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        job.status = JobStatus.APPLIED
        job.applied_at = datetime.utcnow()
        await session.commit()
        return {"success": True, "job_id": job_id}


# Add datetime import at the top
from datetime import datetime


# === ENHANCED JOB MATCHING ENDPOINTS ===

@app.post("/jobs/{job_id}/analyze")
async def analyze_job_match(job_id: int):
    """
    Analyze how well user's resume matches this job
    Uses AI to calculate match scores and identify skill gaps
    """
    from database.engine import async_session
    from database.models import Job, Resume, JobMatch
    from sqlalchemy import select
    from agents.job_matcher.matcher import job_matcher
    import json
    
    async with async_session() as session:
        # Get job
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get user's latest resume (simplified - should use auth)
        result = await session.execute(
            select(Resume).order_by(Resume.created_at.desc()).limit(1)
        )
        resume = result.scalar_one_or_none()
        if not resume:
            raise HTTPException(status_code=404, detail="No resume found. Please upload a resume first.")
        
        # Prepare data
        resume_skills = resume.skills if isinstance(resume.skills, list) else []
        resume_data = {
            'skills': resume_skills,
            'experience_years': resume.experience_years or 0,
            'education': resume.text_content[:500] if resume.text_content else '',
            'name': resume.filename or 'User',
            'email': 'user@example.com',
            'phone': '',
            'location': '',
            'experience': resume.text_content[:1000] if resume.text_content else '',
            'current_role': 'Professional'
        }
        
        job_data = {
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'description': job.description or '',
            'requirements': job.description or ''
        }
        
        # Calculate match
        match_result = job_matcher.calculate_match_score(resume_data, job_data)
        
        # Save to database
        job_match = JobMatch(
            job_id=job_id,
            user_id=resume.user_id,
            overall_score=match_result['overall_score'],
            skill_score=match_result['skill_score'],
            experience_score=match_result['experience_score'],
            education_score=match_result['education_score'],
            matched_skills=match_result['matched_skills'],
            missing_skills=match_result['missing_skills'],
            why_good_fit=match_result['why_good_fit']
        )
        session.add(job_match)
        
        # Update job with match score
        job.match_score = match_result['overall_score']
        
        await session.commit()
        
        return match_result


@app.post("/jobs/{job_id}/generate-resume")
async def generate_custom_resume(job_id: int):
    """
    Generate custom resume tailored for this specific job
    Uses AI to optimize content and create ATS-friendly document
    """
    from database.engine import async_session
    from database.models import Job, Resume, JobMatch, CustomResume
    from sqlalchemy import select
    from agents.resume_generator.generator import resume_generator
    
    async with async_session() as session:
        # Get job
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get job match
        result = await session.execute(
            select(JobMatch).where(JobMatch.job_id == job_id).order_by(JobMatch.created_at.desc()).limit(1)
        )
        job_match = result.scalar_one_or_none()
        if not job_match:
            raise HTTPException(
                status_code=404, 
                detail="Please analyze job match first by calling /jobs/{job_id}/analyze"
            )
        
        # Get resume
        result = await session.execute(
            select(Resume).order_by(Resume.created_at.desc()).limit(1)
        )
        resume = result.scalar_one_or_none()
        if not resume:
            raise HTTPException(status_code=404, detail="No resume found")
        
        # Prepare data
        resume_skills = resume.skills if isinstance(resume.skills, list) else []
        resume_data = {
            'name': 'John Doe',  # Should come from user profile
            'email': 'user@example.com',
            'phone': '+1234567890',
            'location': 'City, State',
            'skills': resume_skills,
            'experience_years': resume.experience_years or 0,
            'current_role': 'Professional',
            'experience': resume.text_content[:1000] if resume.text_content else '',
            'education': 'Your Education'
        }
        
        job_data = {
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'description': job.description or '',
            'requirements': job.description or ''
        }
        
        match_data = {
            'matched_skills': job_match.matched_skills if isinstance(job_match.matched_skills, list) else [],
            'missing_skills': job_match.missing_skills if isinstance(job_match.missing_skills, list) else []
        }
        
        # Generate resume
        filename = resume_generator.generate_custom_resume(resume_data, job_data, match_data)
        
        # Save to database
        custom_resume = CustomResume(
            job_id=job_id,
            user_id=resume.user_id,
            resume_docx_path=filename,
            ats_optimized=True
        )
        session.add(custom_resume)
        await session.commit()
        
        return {
            "message": "Resume generated successfully",
            "filename": filename,
            "download_url": f"/download-resume/{custom_resume.id}"
        }


@app.get("/download-resume/{resume_id}")
async def download_custom_resume(resume_id: int):
    """
    Download generated custom resume
    """
    from database.engine import async_session
    from database.models import CustomResume
    from sqlalchemy import select
    
    async with async_session() as session:
        result = await session.execute(
            select(CustomResume).where(CustomResume.id == resume_id)
        )
        custom_resume = result.scalar_one_or_none()
        if not custom_resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        if not os.path.exists(custom_resume.resume_docx_path):
            raise HTTPException(status_code=404, detail="Resume file not found on disk")
        
        return FileResponse(
            custom_resume.resume_docx_path,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            filename=f"resume_{custom_resume.job_id}.docx"
        )


# === VISION-GUIDED SCRAPING ENDPOINTS (V2) ===

class VisionScrapeRequest(BaseModel):
    portal: str
    query: str
    location: str = ""
    max_jobs: int = 100


class VisionBatchRequest(BaseModel):
    query: str
    location: str = ""
    portals: Optional[List[str]] = None
    max_jobs_per_portal: int = 100


vision_orchestrator = None


@app.post("/api/v2/scrape/portal")
async def scrape_portal_vision(req: VisionScrapeRequest):
    """Scrape a single job portal using vision-guided navigation."""
    global vision_orchestrator
    if vision_orchestrator is None:
        from agents.vision_scraper.scraping_orchestrator import ScrapingOrchestrator
        vision_orchestrator = ScrapingOrchestrator()

    try:
        result = await vision_orchestrator.scrape_portal(
            portal_name=req.portal,
            query=req.query,
            location=req.location,
            max_jobs=req.max_jobs,
        )
        return {
            "success": result.status == NavigationStatus.SUCCESS,
            "portal": result.portal_name,
            "status": result.status.value,
            "jobs_count": len(result.jobs),
            "jobs": [job.model_dump() for job in result.jobs],
            "steps_taken": result.steps_taken,
            "time_elapsed_ms": result.time_elapsed_ms,
            "error": result.error_message,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v2/scrape/all-portals")
async def scrape_all_portals_vision(req: VisionBatchRequest):
    """Scrape multiple job portals using vision-guided navigation."""
    global vision_orchestrator
    if vision_orchestrator is None:
        from agents.vision_scraper.scraping_orchestrator import ScrapingOrchestrator
        vision_orchestrator = ScrapingOrchestrator()

    try:
        results = await vision_orchestrator.scrape_all_portals(
            query=req.query,
            location=req.location,
            portal_names=req.portals,
            max_jobs_per_portal=req.max_jobs_per_portal,
        )
        summary = {
            portal: {
                "status": r.status.value,
                "jobs_count": len(r.jobs),
                "time_elapsed_ms": r.time_elapsed_ms,
                "error": r.error_message,
            }
            for portal, r in results.items()
        }
        total_jobs = sum(len(r.jobs) for r in results.values())
        return {
            "success": True,
            "total_jobs": total_jobs,
            "portals_scraped": len(results),
            "summary": summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/scrape/status")
async def scrape_status():
    """Get rate limit status and orchestrator health."""
    global vision_orchestrator
    if vision_orchestrator is None:
        return {"status": "not_initialized"}

    return {
        "rate_limits": vision_orchestrator.rate_limiter.get_rate_limit_status(),
        "browser_active": not vision_orchestrator.browser.is_browser_crashed(),
    }


@app.on_event("shutdown")
async def shutdown_vision():
    """Clean up vision orchestrator on shutdown."""
    global vision_orchestrator
    if vision_orchestrator:
        await vision_orchestrator.close()


# === PHASE 3: RECRUITER INTELLIGENCE ENDPOINTS ===

class RecruiterRequest(BaseModel):
    job_id: int
    resume_summary: str = ""


class CompanyContactRequest(BaseModel):
    company_name: str
    website: str = ""
    role_hint: str = "recruiter"


class OutreachRequest(BaseModel):
    job_id: int
    recruiter_name: str = ""
    recruiter_email: str = ""
    resume_summary: str = ""
    message_type: str = "email"


recruiter_intelligence = None


@app.post("/api/v3/recruiter/analyze-job")
async def analyze_job_recruiter(req: RecruiterRequest):
    """Full recruiter intelligence analysis for a job."""
    global recruiter_intelligence
    if recruiter_intelligence is None:
        from agents.recruiter_intelligence import RecruiterIntelligence
        recruiter_intelligence = RecruiterIntelligence()

    from database.engine import async_session
    from database.models import Job
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(select(Job).where(Job.id == req.job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        job_data = {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description or "",
            "source_url": job.source_url or "",
        }

        analysis = await recruiter_intelligence.analyze_job_opportunity(
            job_data=job_data,
            resume_summary=req.resume_summary,
        )

        recruiters_to_save = analysis.get("recruiters", [])
        if recruiters_to_save:
            from database.models import Recruiter
            for r in recruiters_to_save:
                recruiter = Recruiter(
                    name=r.get("name", ""),
                    role=r.get("role", ""),
                    company=job.company,
                    linkedin_url=r.get("linkedin_url", ""),
                    email=r.get("email", ""),
                    source=r.get("source", "ai_search"),
                    confidence=r.get("confidence", 0.5),
                    job_id=job.id,
                )
                session.add(recruiter)
            await session.commit()

        return {
            "success": True,
            "job_id": req.job_id,
            "company_name": analysis.get("company_name", ""),
            "is_actively_hiring": analysis.get("is_actively_hiring", False),
            "hiring_signals": analysis.get("hiring_signals", []),
            "tech_stack": analysis.get("tech_stack", []),
            "company_priority": analysis.get("company_priority", "cold"),
            "recruiters_found": analysis.get("recruiters_found", 0),
            "recruiters": analysis.get("recruiters", []),
            "outreach_draft": analysis.get("outreach_draft", ""),
            "company_intelligence": analysis.get("company_intelligence", {}),
        }


@app.post("/api/v3/recruiter/find-contacts")
async def find_company_contacts(req: CompanyContactRequest):
    """Find contacts for a specific company."""
    global recruiter_intelligence
    if recruiter_intelligence is None:
        from agents.recruiter_intelligence import RecruiterIntelligence
        recruiter_intelligence = RecruiterIntelligence()

    contacts = await recruiter_intelligence.find_contacts_for_company(
        company_name=req.company_name,
        website=req.website,
        role_hint=req.role_hint,
    )

    return {
        "success": True,
        "company": req.company_name,
        "contacts_found": len(contacts),
        "contacts": contacts,
    }


@app.post("/api/v3/recruiter/generate-outreach")
async def generate_outreach(req: OutreachRequest):
    """Generate personalized outreach message."""
    global recruiter_intelligence
    if recruiter_intelligence is None:
        from agents.recruiter_intelligence import RecruiterIntelligence
        recruiter_intelligence = RecruiterIntelligence()

    from database.engine import async_session
    from database.models import Job
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(select(Job).where(Job.id == req.job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        job_data = {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description or "",
        }

        recruiter = {
            "name": req.recruiter_name or "Hiring Manager",
            "email": req.recruiter_email,
        }

        message = await recruiter_intelligence.generate_outreach(
            job=job_data,
            recruiter=recruiter,
            resume_summary=req.resume_summary,
            message_type=req.message_type,
        )

        return {
            "success": True,
            "message": message,
            "recipient": req.recruiter_name or "Hiring Manager",
            "job": job.title,
        }


@app.get("/api/v3/recruiter/job/{job_id}")
async def get_job_recruiters(job_id: int):
    """Get saved recruiters for a specific job."""
    from database.engine import async_session
    from database.models import Recruiter
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(
            select(Recruiter).where(Recruiter.job_id == job_id).order_by(Recruiter.confidence.desc())
        )
        recruiters = result.scalars().all()

        return {
            "job_id": job_id,
            "recruiters": [
                {
                    "id": r.id,
                    "name": r.name,
                    "role": r.role,
                    "company": r.company,
                    "linkedin_url": r.linkedin_url,
                    "email": r.email,
                    "source": r.source,
                    "confidence": r.confidence,
                }
                for r in recruiters
            ],
        }


# === PHASE 4: OUTREACH AUTOMATION ENDPOINTS ===

class SendEmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str
    html_body: Optional[str] = None
    job_id: Optional[int] = None
    recruiter_id: Optional[int] = None
    from_name: str = ""
    auto_follow_up: bool = True


class JobOutreachRequest(BaseModel):
    job_id: int
    recruiter_email: str
    recruiter_name: str = ""
    resume_summary: str = ""
    from_name: str = ""


class FollowUpProcessRequest(BaseModel):
    resume_summary: str = ""
    from_name: str = ""


outreach_orchestrator = None


@app.post("/api/v4/outreach/send")
async def send_outreach_email(req: SendEmailRequest):
    """Send a single outreach email."""
    global outreach_orchestrator
    if outreach_orchestrator is None:
        from outreach.orchestrator import OutreachOrchestrator
        outreach_orchestrator = OutreachOrchestrator()

    result = await outreach_orchestrator.send_outreach_email(
        to_email=req.to_email,
        subject=req.subject,
        body=req.body,
        html_body=req.html_body,
        job_id=req.job_id,
        recruiter_id=req.recruiter_id,
        from_name=req.from_name,
        auto_follow_up=req.auto_follow_up,
    )
    return result


@app.post("/api/v4/outreach/job")
async def send_job_outreach(req: JobOutreachRequest):
    """Generate and send outreach email for a specific job."""
    global outreach_orchestrator
    if outreach_orchestrator is None:
        from outreach.orchestrator import OutreachOrchestrator
        outreach_orchestrator = OutreachOrchestrator()

    from database.engine import async_session
    from database.models import Job
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(select(Job).where(Job.id == req.job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        job_data = {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description or "",
        }

        recruiter = {
            "id": req.recruiter_id,
            "name": req.recruiter_name or "Hiring Manager",
            "email": req.recruiter_email,
        }

        result = await outreach_orchestrator.send_job_outreach(
            job=job_data,
            recruiter=recruiter,
            resume_summary=req.resume_summary,
            from_name=req.from_name,
        )
        return result


@app.post("/api/v4/outreach/process-followups")
async def process_follow_ups(req: FollowUpProcessRequest):
    """Process pending follow-up emails."""
    global outreach_orchestrator
    if outreach_orchestrator is None:
        from outreach.orchestrator import OutreachOrchestrator
        outreach_orchestrator = OutreachOrchestrator()

    results = await outreach_orchestrator.process_follow_ups(
        jobs_data={},
        resume_summary=req.resume_summary,
        from_name=req.from_name,
    )
    return {
        "processed": len(results),
        "results": results,
    }


@app.get("/api/v4/outreach/stats")
async def get_outreach_stats():
    """Get email outreach statistics."""
    global outreach_orchestrator
    if outreach_orchestrator is None:
        from outreach.orchestrator import OutreachOrchestrator
        outreach_orchestrator = OutreachOrchestrator()

    return outreach_orchestrator.get_email_stats()


@app.get("/api/v4/outreach/history")
async def get_outreach_history(job_id: Optional[int] = None):
    """Get email outreach history."""
    global outreach_orchestrator
    if outreach_orchestrator is None:
        from outreach.orchestrator import OutreachOrchestrator
        outreach_orchestrator = OutreachOrchestrator()

    return {
        "emails": outreach_orchestrator.get_email_history(job_id=job_id),
    }


@app.get("/api/v4/outreach/email/{email_id}")
async def get_email_record(email_id: str):
    """Get a specific email record."""
    global outreach_orchestrator
    if outreach_orchestrator is None:
        from outreach.orchestrator import OutreachOrchestrator
        outreach_orchestrator = OutreachOrchestrator()

    record = outreach_orchestrator.get_email_record(email_id)
    if not record:
        raise HTTPException(status_code=404, detail="Email record not found")
    return record


# === PHASE 5: AUTO-APPLY AGENT ENDPOINTS ===

class AutoApplyRequest(BaseModel):
    job_id: int
    resume_summary: str = ""
    resume_file_path: Optional[str] = None
    user_review_required: bool = True


class FormAnalyzeRequest(BaseModel):
    apply_url: str
    portal: str = ""


auto_apply_agent = None


@app.post("/api/v5/auto-apply/submit")
async def submit_application(req: AutoApplyRequest):
    """Automatically apply to a job."""
    global auto_apply_agent
    if auto_apply_agent is None:
        from agents.browser_agent.browser_controller import BrowserController
        from agents.auto_apply.auto_apply_agent import AutoApplyAgent
        browser = BrowserController(headless=False)
        auto_apply_agent = AutoApplyAgent(browser=browser)

    from database.engine import async_session
    from database.models import Job, ApplicationSubmission
    from sqlalchemy import select
    import datetime

    async with async_session() as session:
        result = await session.execute(select(Job).where(Job.id == req.job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if not job.apply_url and not job.source_url:
            raise HTTPException(status_code=400, detail="No application URL available")

        apply_url = job.apply_url or job.source_url

        resume_data = {
            "name": "User",
            "email": "",
            "phone": "",
            "location": "",
            "skills": [],
            "experience_years": 0,
            "current_role": "Professional",
            "experience": req.resume_summary,
        }

        job_data = {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description or "",
        }

        submission = ApplicationSubmission(
            job_id=req.job_id,
            user_id=1,
            apply_url=apply_url,
            portal=job.source or "unknown",
            status="in_progress",
            started_at=datetime.datetime.utcnow(),
        )
        session.add(submission)
        await session.commit()

        try:
            apply_result = await auto_apply_agent.apply_to_job(
                apply_url=apply_url,
                resume_data=resume_data,
                job_data=job_data,
                resume_file_path=req.resume_file_path,
                user_review_required=req.user_review_required,
            )

            submission.status = "submitted" if apply_result.get("submitted") else "needs_review"
            submission.total_fields = apply_result.get("fields_filled", 0)
            submission.fields_filled = apply_result.get("fields_filled", 0)
            submission.questions_answered = apply_result.get("questions_answered", 0)
            submission.fields_needing_review = apply_result.get("fields_needing_review", [])
            submission.time_elapsed_ms = apply_result.get("time_elapsed_ms", 0)
            submission.completed_at = datetime.datetime.utcnow()

            if apply_result.get("errors"):
                submission.error_message = "; ".join(apply_result["errors"])
                submission.status = "failed"

            await session.commit()

            return {
                "success": apply_result.get("success", False),
                "submission_id": submission.id,
                "status": submission.status,
                "fields_filled": submission.fields_filled,
                "questions_answered": submission.questions_answered,
                "time_elapsed_ms": submission.time_elapsed_ms,
                "errors": apply_result.get("errors", []),
                "fields_needing_review": submission.fields_needing_review,
            }

        except Exception as e:
            submission.status = "failed"
            submission.error_message = str(e)
            submission.completed_at = datetime.datetime.utcnow()
            await session.commit()
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v5/auto-apply/analyze-form")
async def analyze_application_form(req: FormAnalyzeRequest):
    """Analyze an application form without submitting."""
    global auto_apply_agent
    if auto_apply_agent is None:
        from agents.browser_agent.browser_controller import BrowserController
        from agents.auto_apply.auto_apply_agent import AutoApplyAgent
        browser = BrowserController(headless=False)
        auto_apply_agent = AutoApplyAgent(browser=browser)

    try:
        await auto_apply_agent.browser.go_to(req.apply_url, timeout=30000)
        await auto_apply_agent.browser.wait(3)

        form_analysis = await auto_apply_agent.form_analyzer.analyze_form_dom(
            auto_apply_agent.browser.page
        )

        return {
            "success": True,
            "url": form_analysis.url,
            "portal": form_analysis.portal,
            "total_fields": form_analysis.total_fields,
            "can_auto_fill": form_analysis.can_auto_fill,
            "estimated_fill_time_seconds": form_analysis.estimated_fill_time_seconds,
            "fields_needing_review": form_analysis.fields_needing_review,
            "screening_questions": [
                {
                    "question": q.question_text,
                    "type": q.question_type,
                    "needs_review": q.needs_review,
                }
                for q in form_analysis.screening_questions
            ],
            "file_uploads": [
                {"label": f.label, "required": f.required}
                for f in form_analysis.file_uploads
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v5/auto-apply/submissions")
async def get_application_submissions(status: Optional[str] = None):
    """Get application submission history."""
    from database.engine import async_session
    from database.models import ApplicationSubmission
    from sqlalchemy import select

    async with async_session() as session:
        query = select(ApplicationSubmission).order_by(ApplicationSubmission.created_at.desc())
        if status:
            query = query.where(ApplicationSubmission.status == status)
        result = await session.execute(query)
        submissions = result.scalars().all()

        return {
            "submissions": [
                {
                    "id": s.id,
                    "job_id": s.job_id,
                    "portal": s.portal,
                    "status": s.status,
                    "fields_filled": s.fields_filled,
                    "questions_answered": s.questions_answered,
                    "time_elapsed_ms": s.time_elapsed_ms,
                    "error_message": s.error_message,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s in submissions
            ],
        }


@app.get("/api/v5/auto-apply/submission/{submission_id}")
async def get_submission_detail(submission_id: int):
    """Get details of a specific application submission."""
    from database.engine import async_session
    from database.models import ApplicationSubmission
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(
            select(ApplicationSubmission).where(ApplicationSubmission.id == submission_id)
        )
        submission = result.scalar_one_or_none()
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        return {
            "id": submission.id,
            "job_id": submission.job_id,
            "apply_url": submission.apply_url,
            "portal": submission.portal,
            "status": submission.status,
            "total_fields": submission.total_fields,
            "fields_filled": submission.fields_filled,
            "questions_answered": submission.questions_answered,
            "fields_needing_review": submission.fields_needing_review,
            "started_at": submission.started_at.isoformat() if submission.started_at else None,
            "completed_at": submission.completed_at.isoformat() if submission.completed_at else None,
            "time_elapsed_ms": submission.time_elapsed_ms,
            "error_message": submission.error_message,
            "confirmation_number": submission.confirmation_number,
        }


# ============================================================
# UI-TARS Autonomous Agent (Phase 6)
# ============================================================

class UITarsTaskRequest(BaseModel):
    task: str
    start_url: Optional[str] = "https://www.google.com"
    max_steps: int = 25


ui_tars_browser = None
ui_tars_lock = asyncio.Lock()


async def get_ui_tars_browser():
    """Get or create UI-TARS browser instance."""
    global ui_tars_browser
    if ui_tars_browser is None or ui_tars_browser.is_browser_crashed():
        from agents.browser_agent.browser_controller import BrowserController
        ui_tars_browser = BrowserController(headless=False)
        await ui_tars_browser.start()
    return ui_tars_browser


async def close_ui_tars_browser():
    """Close UI-TARS browser instance."""
    global ui_tars_browser
    if ui_tars_browser:
        try:
            await ui_tars_browser.close()
        except:
            pass
        ui_tars_browser = None


@app.post("/api/v6/ui-tars/run")
async def run_ui_tars_task(request: UITarsTaskRequest):
    """
    Run UI-TARS autonomous agent on any task.
    
    Give it any natural language task like:
    - "Open YouTube and search for 'sao paulo song'"
    - "Book me a flight from NYC to LA"
    - "Fill out this job application form"
    """
    try:
        from agents.vision_scraper.ui_tars_agent import UITarsAgent
        
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        if not mistral_api_key:
            raise HTTPException(status_code=500, detail="MISTRAL_API_KEY not configured")
        
        async with ui_tars_lock:
            try:
                browser = await get_ui_tars_browser()
                agent = UITarsAgent(browser, mistral_api_key, max_steps=request.max_steps)
                result = await agent.run(request.task, start_url=request.start_url)
                
                return {
                    "status": result.get("status"),
                    "task": request.task,
                    "steps_taken": result.get("steps", 0),
                    "error": result.get("error"),
                    "action_history": [
                        {
                            "step": h["step"],
                            "action": h["parsed"].get("action_type"),
                            "thought": h["parsed"].get("thought", "")[:200],
                        }
                        for h in result.get("history", [])
                    ],
                }
            finally:
                # Always close browser after task completes
                await close_ui_tars_browser()
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Ensure browser is closed even on error
        await close_ui_tars_browser()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v6/ui-tars/close")
async def close_ui_tars():
    """Force close UI-TARS browser if stuck."""
    await close_ui_tars_browser()
    return {"status": "browser_closed"}


@app.post("/api/v6/ui-tars/run-stream")
async def run_ui_tars_stream(request: UITarsTaskRequest):
    """Run UI-TARS task with real-time streaming updates."""
    from agents.vision_scraper.ui_tars_agent import UITarsAgent
    
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    if not mistral_api_key:
        raise HTTPException(status_code=500, detail="MISTRAL_API_KEY not configured")
    
    async def event_stream():
        async with ui_tars_lock:
            browser = await get_ui_tars_browser()
            agent = UITarsAgent(browser, mistral_api_key, max_steps=request.max_steps)
            
            # Override run to yield events
            if request.start_url:
                await browser.go_to(request.start_url)
                await browser.wait(2)
            
            viewport = browser.page.viewport_size
            if viewport:
                agent._viewport_width = viewport.get("width", 1400)
                agent._viewport_height = viewport.get("height", 900)
            
            history_text = ""
            last_action = ""
            same_action_count = 0
            
            for step in range(1, request.max_steps + 1):
                if browser.is_browser_crashed():
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Browser crashed'})}\n\n"
                    return
                
                screenshot = await browser.take_screenshot()
                if isinstance(screenshot, str) and screenshot.startswith("screenshot_error"):
                    yield f"data: {json.dumps({'type': 'error', 'message': f'Screenshot failed: {screenshot}'})}\n\n"
                    return
                
                import base64
                if isinstance(screenshot, bytes):
                    screenshot_b64 = base64.b64encode(screenshot).decode("utf-8")
                else:
                    screenshot_b64 = screenshot
                
                try:
                    response_text = agent._call_mistral(screenshot_b64, request.task, history_text)
                    parsed = agent._parse_action(response_text)
                    
                    yield f"data: {json.dumps({'type': 'step', 'step': step, 'response': response_text[:500], 'action': parsed.get('action_type')})}\n\n"
                    
                    history_text += f"Step {step}: {response_text}\n"
                    agent._history.append({"step": step, "response": response_text, "parsed": parsed})
                    
                    current_action = f"{parsed.get('action_type')}_{json.dumps(parsed.get('action_inputs', {}))}"
                    if current_action == last_action:
                        same_action_count += 1
                        if same_action_count >= 3:
                            yield f"data: {json.dumps({'type': 'complete', 'status': 'loop_detected', 'steps': step})}\n\n"
                            return
                    else:
                        same_action_count = 0
                    last_action = current_action
                    
                    await agent._execute_action(parsed)
                    
                    if parsed.get("action_type") == "finished":
                        yield f"data: {json.dumps({'type': 'complete', 'status': 'success', 'steps': step})}\n\n"
                        return
                    
                    await browser.wait(2)
                    
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                    return
            
            yield f"data: {json.dumps({'type': 'complete', 'status': 'timeout', 'steps': request.max_steps})}\n\n"
    
    from fastapi.responses import StreamingResponse
    return StreamingResponse(event_stream(), media_type="text/event-stream")
