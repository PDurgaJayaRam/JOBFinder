"""Job discovery agent - uses AI browser agent to interact with websites."""
import os
import sys
import json
import subprocess
from typing import List, Dict, Any


class JobDiscoveryAgent:
    """Searches job boards using AI browser agent that can interact with websites."""

    def __init__(self):
        self.headless = os.getenv("PLAYWRIGHT_HEADLESS", "false").lower() == "true"

    @property
    def project_root(self):
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    async def search_jobs(
        self,
        keywords: List[str],
        locations: List[str],
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Run AI browser agent in a subprocess."""
        query = " ".join(keywords)
        location = " ".join(locations)

        try:
            script_path = os.path.join(self.project_root, "agents", "browser_agent", "standalone.py")
            result = subprocess.run(
                [sys.executable, script_path, query, location, str(max_results), str(self.headless).lower()],
                capture_output=True, text=True, timeout=120,
                cwd=self.project_root
            )

            # Print agent logs for debugging
            for line in result.stdout.split('\n'):
                if line.startswith('[LOG]') or line.startswith('[BROWSER_AGENT]'):
                    print(line, flush=True)

            # Parse JSON output (last line)
            for line in reversed(result.stdout.split('\n')):
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    jobs = json.loads(line)
                    if jobs:
                        print(f"Browser agent found {len(jobs)} jobs", flush=True)
                        return jobs

            # Check stderr for errors
            if result.stderr:
                print(f"Browser agent stderr: {result.stderr[:500]}", flush=True)

        except subprocess.TimeoutExpired:
            print("Browser agent timed out (180s), using fallback", flush=True)
        except Exception as e:
            print(f"Browser agent error: {e}", flush=True)

        return self._get_sample_jobs(query, location, max_results)

    def _get_sample_jobs(self, query: str, location: str, limit: int) -> List[Dict]:
        return [
            {
                "title": f"{query} Developer - Fresher", "company": "Tech Corp India",
                "location": location, "source": "sample",
                "source_url": "https://www.indeed.com/jobs", "apply_url": "https://www.indeed.com/jobs",
                "salary": "3-5 LPA", "experience_required": "0-1 years",
                "skills_required": ["Python", "SQL"], "description": "",
                "remote": False, "walk_in": True, "internship": False,
            },
            {
                "title": f"Junior {query} Engineer", "company": "Data Insights Pvt Ltd",
                "location": location, "source": "sample",
                "source_url": "https://www.naukri.com", "apply_url": "https://www.naukri.com",
                "salary": "4-6 LPA", "experience_required": "0-2 years",
                "skills_required": ["Python", "SQL"], "description": "",
                "remote": False, "walk_in": False, "internship": False,
            },
            {
                "title": f"{query} Intern", "company": "StartupHub",
                "location": location, "source": "sample",
                "source_url": "https://www.linkedin.com/jobs", "apply_url": "https://www.linkedin.com/jobs",
                "salary": "2-3 LPA", "experience_required": "Fresher",
                "skills_required": ["Python"], "description": "",
                "remote": True, "walk_in": False, "internship": True,
            },
        ][:limit]

    async def fetch_job_details(self, job_url: str) -> Dict[str, Any]:
        return {"description": ""}