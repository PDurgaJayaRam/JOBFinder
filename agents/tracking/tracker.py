"""Application tracking agent - stores and retrieves application status."""
from typing import Dict, Any, List
from datetime import datetime


class TrackingAgent:
    """Tracks job applications and lead outreach statuses."""

    def __init__(self):
        # In-memory store for MVP; replace with DB in production
        self._applications: List[Dict[str, Any]] = []
        self._outreach: List[Dict[str, Any]] = []

    async def track_application(self, job: Dict[str, Any], status: str = "applied", notes: str = ""):
        record = {
            "id": len(self._applications) + 1,
            "job_title": job.get("title", ""),
            "company": job.get("company", ""),
            "status": status,
            "source": job.get("source", ""),
            "apply_url": job.get("apply_url", ""),
            "match_score": job.get("match_score"),
            "notes": notes,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._applications.append(record)
        return record

    async def update_status(self, app_id: int, new_status: str, notes: str = ""):
        for app in self._applications:
            if app["id"] == app_id:
                app["status"] = new_status
                app["notes"] = notes or app["notes"]
                app["updated_at"] = datetime.utcnow().isoformat()
                return app
        return None

    async def get_applications(self, status: str = None) -> List[Dict[str, Any]]:
        if status:
            return [a for a in self._applications if a["status"] == status]
        return self._applications.copy()

    async def track_outreach(self, lead: Dict[str, Any], message: str, recipient: str):
        record = {
            "id": len(self._outreach) + 1,
            "company": lead.get("name", ""),
            "recipient": recipient,
            "message": message,
            "status": "draft",
            "created_at": datetime.utcnow().isoformat(),
        }
        self._outreach.append(record)
        return record

    async def get_outreach(self) -> List[Dict[str, Any]]:
        return self._outreach.copy()

    async def get_analytics(self) -> Dict[str, Any]:
        total_apps = len(self._applications)
        status_counts = {}
        for app in self._applications:
            status_counts[app["status"]] = status_counts.get(app["status"], 0) + 1

        total_outreach = len(self._outreach)
        return {
            "total_applications": total_apps,
            "status_breakdown": status_counts,
            "total_outreach": total_outreach,
            "last_updated": datetime.utcnow().isoformat(),
        }
