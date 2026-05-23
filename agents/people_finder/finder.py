"""People finder agent - discovers recruiters and hiring managers from public sources."""
import re
import json
import httpx
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from ai.ai_client import get_ai_client
from ai.prompts import RECRUITER_SEARCH_PROMPT


class PeopleFinderAgent:
    """Finds publicly available professional contacts. Only uses public data."""

    def __init__(self):
        self.ai = get_ai_client()
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    async def find_people(self, company: Dict[str, Any], role_hint: str = "") -> List[Dict[str, Any]]:
        """Find relevant people for a given company."""
        name = company.get("name") or company.get("company_name", "")
        website = company.get("website", "")
        size = company.get("size") or company.get("company_size", "")

        context = f"Company: {name}\nWebsite: {website}\nSize: {size}\nLooking for: {role_hint or 'recruiters, hiring managers, HR'}"

        messages = [
            {"role": "system", "content": RECRUITER_SEARCH_PROMPT},
            {"role": "user", "content": context},
        ]

        try:
            raw = await self.ai.chat_completion(messages=messages, temperature=0.3, json_mode=True)
            people = json.loads(raw)
            if isinstance(people, list):
                return people
            return []
        except Exception:
            return []

    async def search_linkedin_public(self, company_name: str, role: str = "recruiter") -> List[Dict[str, Any]]:
        """Searches public LinkedIn pages for names (ethical, no login required)."""
        results = []
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=15.0, follow_redirects=True) as client:
                query = f"{company_name} {role} site:linkedin.com/in"
                resp = await client.get(f"https://www.google.com/search?q={query}&num=10")
                soup = BeautifulSoup(resp.text, "html.parser")
                
                for link in soup.select("a[href*='linkedin.com/in']")[:5]:
                    href = link.get("href", "")
                    if href.startswith("/url?q="):
                        href = href.split("/url?q=")[1].split("&")[0]
                    
                    name_text = link.get_text(strip=True)
                    if name_text and len(name_text) > 3:
                        results.append({
                            "name": name_text,
                            "role": role,
                            "linkedin_url": href,
                            "source": "google_linkedin_search",
                            "confidence": 0.5,
                        })
        except Exception:
            pass
        return results

    async def find_email_by_pattern(self, company_name: str, person_name: str, website: str = "") -> Optional[str]:
        """Generate likely email using common corporate patterns."""
        name_parts = person_name.lower().split()
        if len(name_parts) < 2:
            return None
        
        first = name_parts[0]
        last = name_parts[-1]
        domain = self._extract_domain(website or company_name)
        
        if not domain:
            return None
        
        patterns = [
            f"{first}.{last}@{domain}",
            f"{first[0]}{last}@{domain}",
            f"{first}{last}@{domain}",
            f"{last}{first[0]}@{domain}",
            f"{first}@{domain}",
            f"{last}@{domain}",
        ]
        return patterns[0]

    def _extract_domain(self, text: str) -> Optional[str]:
        """Extract domain from URL or company name."""
        if text.startswith("http"):
            match = re.search(r"https?://(?:www\.)?([^/]+)", text)
            if match:
                return match.group(1).rstrip("/")
        
        clean = re.sub(r'[^a-zA-Z0-9\s-]', '', text.lower())
        words = clean.split()
        if len(words) >= 2:
            return f"{''.join(words)}.com"
        elif words:
            return f"{words[0]}.com"
        return None

    async def scrape_company_team_page(self, website: str) -> List[Dict[str, Any]]:
        """Scrape company 'About' or 'Team' page for employee names."""
        results = []
        if not website:
            return results
        
        team_urls = [
            f"{website}/about",
            f"{website}/team",
            f"{website}/about-us",
            f"{website}/our-team",
            f"{website}/leadership",
        ]
        
        async with httpx.AsyncClient(headers=self.headers, timeout=15.0, follow_redirects=True) as client:
            for url in team_urls:
                try:
                    resp = await client.get(url)
                    soup = BeautifulSoup(resp.text, "html.parser")
                    
                    for tag in soup.find_all(["h2", "h3", "h4"]):
                        text = tag.get_text(strip=True)
                        if self._looks_like_name(text):
                            results.append({
                                "name": text,
                                "role": "team_member",
                                "source": "company_website",
                                "confidence": 0.4,
                            })
                    
                    if results:
                        break
                except Exception:
                    continue
        
        return results

    def _looks_like_name(self, text: str) -> bool:
        """Heuristic check if text looks like a person's name."""
        if len(text) < 5 or len(text) > 50:
            return False
        words = text.split()
        if len(words) < 2 or len(words) > 4:
            return False
        return all(w[0].isupper() for w in words if w)

    async def find_recruiters_for_job(self, job_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find recruiters/hiring managers associated with a specific job."""
        company_name = job_data.get("company", "")
        if not company_name:
            return []
        
        all_people = []
        
        linkedin_results = await self.search_linkedin_public(company_name, "recruiter")
        all_people.extend(linkedin_results)
        
        hr_results = await self.search_linkedin_public(company_name, "hiring manager")
        all_people.extend(hr_results)
        
        for person in all_people:
            if not person.get("email") and job_data.get("source_url"):
                website = self._extract_website_from_job(job_data)
                person["email"] = await self.find_email_by_pattern(
                    company_name, person["name"], website
                )
        
        seen = set()
        unique = []
        for p in all_people:
            key = p.get("name", "") + p.get("linkedin_url", "")
            if key not in seen:
                seen.add(key)
                unique.append(p)
        
        return unique

    def _extract_website_from_job(self, job_data: Dict[str, Any]) -> str:
        """Extract company website from job data."""
        source_url = job_data.get("source_url", "")
        if source_url:
            match = re.search(r"https?://(?:www\.)?([^/]+)", source_url)
            if match:
                return f"https://{match.group(1)}"
        return ""
