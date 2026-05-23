"""AI Brain Agent - NVIDIA GLM4.7 as central decision-maker."""
import asyncio
import json
import os
from typing import List, Dict, Any
import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from ai.ai_client import get_ai_client


class AIBrainAgent:
    """Central AI brain using httpx for job scraping."""

    def __init__(self):
        self.ai = get_ai_client()
        self.ua = UserAgent()
        self.headers = {"User-Agent": self.ua.random}
        self.timeout = httpx.Timeout(30.0, connect=15.0)

    async def decide_scraping_strategy(
        self,
        resume_text: str,
        keywords: List[str],
        locations: List[str],
        max_jobs: int = 20,
    ) -> Dict[str, Any]:
        """AI decides which sites to scrape."""
        prompt = f"""You are an intelligent job search strategist.

RESUME:
{resume_text[:2000]}

TARGET KEYWORDS: {', '.join(keywords)}
LOCATIONS: {', '.join(locations)}
MAX JOBS: {max_jobs}

Return JSON:
{{
  "priority_boards": ["indeed", "naukri"],
  "search_queries": ["Python Data Analyst Hyderabad", "Python Developer Hyderabad"],
  "focus_type": "all",
  "strategy": "..."
}}
"""
        try:
            raw = await self.ai.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                json_mode=True,
            )
            return json.loads(raw)
        except Exception as e:
            return {
                "priority_boards": ["indeed", "naukri"],
                "search_queries": [f"{' '.join(keywords)} {' '.join(locations)}"],
                "focus_type": "all",
                "strategy": f"Default strategy for {keywords} in {locations}",
            }

    async def execute_scraping_with_ai(
        self,
        resume_text: str,
        keywords: List[str],
        locations: List[str],
        max_jobs: int = 20,
    ) -> List[Dict[str, Any]]:
        """AI commands httpx to scrape jobs."""
        strategy = await self.decide_scraping_strategy(resume_text, keywords, locations, max_jobs)
        
        jobs = []
        for board in strategy.get("priority_boards", ["indeed", "naukri"])[:2]:
            try:
                board_jobs = await self._scrape_board_http(board, strategy, keywords, locations, max_jobs // 3)
                jobs.extend(board_jobs)
            except Exception as e:
                print(f"Error scraping {board}: {e}")
        
        return jobs[:max_jobs]

    async def _scrape_board_http(self, board: str, strategy: Dict, keywords: List, locations: List, limit: int) -> List[Dict]:
        """Scrape using httpx."""
        queries = strategy.get("search_queries", [f"{' '.join(keywords)} {' '.join(locations)}"])
        jobs = []
        
        for query in queries[:2]:
            try:
                if board == "indeed":
                    url = f"https://www.indeed.com/jobs?q={query.replace(' ', '+')}"
                    async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout, follow_redirects=True) as client:
                        resp = await client.get(url)
                        soup = BeautifulSoup(resp.text, "lxml")
                        cards = soup.select("div.job_seen_beacon")[:limit]
                        for card in cards:
                            try:
                                title = card.select_one("h2.jobTitle")
                                company = card.select_one("span.companyName")
                                loc = card.select_one("div.companyLocation")
                                link = card.select_one("a.jcs-JobTitle")
                                
                                jobs.append({
                                    "title": title.get_text(strip=True) if title else "",
                                    "company": company.get_text(strip=True) if company else "",
                                    "location": loc.get_text(strip=True) if loc else "",
                                    "source": "indeed",
                                    "source_url": f"https://www.indeed.com{link.get('href', '')}" if link else "",
                                    "apply_url": f"https://www.indeed.com{link.get('href', '')}" if link else "",
                                    "description": "",
                                })
                            except:
                                continue
                elif board == "naukri":
                    url = f"https://www.naukri.com/{query.replace(' ', '-')}-jobs"
                    async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout, follow_redirects=True) as client:
                        resp = await client.get(url)
                        soup = BeautifulSoup(resp.text, "lxml")
                        cards = soup.select("article.jobTuple")[:limit]
                        for card in cards:
                            try:
                                title = card.select_one("a.title")
                                company = card.select_one("a.subTitle")
                                loc = card.select_one("li.location")
                                
                                jobs.append({
                                    "title": title.get_text(strip=True) if title else "",
                                    "company": company.get_text(strip=True) if company else "",
                                    "location": loc.get_text(strip=True) if loc else "",
                                    "source": "naukri",
                                    "source_url": f"https://www.naukri.com{title.get('href', '')}" if title else "",
                                    "apply_url": f"https://www.naukri.com{title.get('href', '')}" if title else "",
                                    "description": "",
                                })
                            except:
                                continue
            except Exception as e:
                print(f"Board {board} error: {e}")
        
        return jobs

    async def decide_application_strategy(
        self,
        job: Dict[str, Any],
        resume_text: str,
        match_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """AI decides whether to apply."""
        prompt = f"""Decide if this job is worth applying to.

JOB: {job.get('title')} at {job.get('company')}
MATCH SCORE: {match_data.get('match_score', 0)}%
GAPS: {match_data.get('missing_required_skills', [])}

RESUME:
{resume_text[:1000]}

Return JSON:
{{
  "should_apply": true,
  "strategy": "direct_apply",
  "cover_letter_angle": "...",
  "confidence": 0.8
}}
"""
        try:
            raw = await self.ai.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                json_mode=True,
            )
            return json.loads(raw)
        except Exception:
            return {
                "should_apply": match_data.get("match_score", 0) >= 60,
                "strategy": "direct_apply",
                "cover_letter_angle": "Strong interest in the role",
                "confidence": 0.5,
            }

    async def execute_application_with_ai(
        self,
        job: Dict[str, Any],
        resume_text: str,
        match_data: Dict[str, Any],
    ) -> bool:
        """AI decides application approach - returns True to indicate we'd apply."""
        strategy = await self.decide_application_strategy(job, resume_text, match_data)
        return strategy.get("should_apply", False)