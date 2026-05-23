"""Celery background tasks."""
from workers.celery_app import celery_app
from agents.orchestrator.orchestrator import AgentOrchestrator


@celery_app.task
def run_job_pipeline_task(resume_text, keywords, locations, auto_apply=False, match_threshold=75.0, max_jobs=20):
    """Run job pipeline in background."""
    import asyncio
    orch = AgentOrchestrator()
    result = asyncio.run(orch.run_job_pipeline(
        resume_text=resume_text,
        keywords=keywords,
        locations=locations,
        auto_apply=auto_apply,
        match_threshold=match_threshold,
        max_jobs=max_jobs,
    ))
    return {
        "jobs_discovered": result.jobs_discovered,
        "jobs_matched": result.jobs_matched,
        "applications_submitted": result.applications_submitted,
        "errors": result.errors,
    }
