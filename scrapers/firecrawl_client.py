"""Firecrawl Integration for Job Scraping."""
import os
import json
import subprocess
import tempfile
from typing import List, Dict, Any, Optional


class FirecrawlClient:
    """Firecrawl client for web scraping, search, and crawling."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY", "")
    
    def _run_command(self, cmd: List[str], timeout: int = 60) -> Dict:
        """Run a firecrawl command and return result."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def search(self, query: str, limit: int = 10, scrape: bool = True) -> List[Dict]:
        """Search the web for jobs."""
        cmd = ["firecrawl", "search", query, "--limit", str(limit)]
        if scrape:
            cmd.append("--scrape")
        
        result = self._run_command(cmd)
        
        if result["success"]:
            try:
                # Parse JSON output
                import re
                json_match = re.search(r'\{[\s\S]*\}', result["output"])
                if json_match:
                    data = json.loads(json_match.group())
                    return data.get("data", {}).get("web", [])
            except:
                pass
        
        # Return empty list if failed
        return []
    
    async def scrape(self, url: str, formats: List[str] = None) -> Dict:
        """Scrape a single URL."""
        if formats is None:
            formats = ["markdown", "links"]
        
        cmd = ["firecrawl", "scrape", url, "--format", ",".join(formats)]
        
        result = self._run_command(cmd)
        
        if result["success"]:
            return {"success": True, "content": result["output"]}
        
        return {"success": False, "error": result.get("error")}
    
    async def crawl(self, url: str, limit: int = 10) -> List[Dict]:
        """Crawl a website for multiple pages."""
        cmd = ["firecrawl", "crawl", url, "--limit", str(limit), "--format", "json"]
        
        result = self._run_command(cmd, timeout=120)
        
        if result["success"]:
            try:
                import re
                json_match = re.search(r'\[[\s\S]*\]', result["output"])
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        return []
    
    async def map(self, url: str, search: str = None) -> List[str]:
        """Find all URLs on a website."""
        cmd = ["firecrawl", "map", url]
        if search:
            cmd.extend(["--search", search])
        
        result = self._run_command(cmd)
        
        if result["success"]:
            try:
                import re
                json_match = re.search(r'\[[\s\S]*\]', result["output"])
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        return []
    
    async def agent(self, task: str, urls: List[str] = None) -> Dict:
        """Use AI agent for complex extraction."""
        cmd = ["firecrawl", "agent", task]
        if urls:
            cmd.extend(urls)
        
        result = self._run_command(cmd, timeout=120)
        
        if result["success"]:
            return {"success": True, "result": result["output"]}
        
        return {"success": False, "error": result.get("error")}


# Fallback to HTTP-based scraping if firecrawl not available
class HTTPScraper:
    """Fallback HTTP scraper using httpx."""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    async def search_jobs(self, query: str, location: str, limit: int = 10) -> List[Dict]:
        """Fallback search using DuckDuckGo."""
        import httpx
        from bs4 import BeautifulSoup
        
        jobs = []
        
        try:
            # Use DuckDuckGo for search
            url = f"https://html.duckduckgo.com/html/?q={query}+jobs+{location}"
            
            async with httpx.AsyncClient(headers=self.headers, timeout=15) as client:
                resp = await client.get(url)
                soup = BeautifulSoup(resp.text, "lxml")
                
                for result in soup.select("div.result")[:limit]:
                    title_el = result.select_one("a.result__a")
                    snippet_el = result.select_one("a.result__snippet")
                    
                    if title_el:
                        jobs.append({
                            "title": title_el.get_text(strip=True),
                            "company": "",
                            "location": location,
                            "source": "web_search",
                            "source_url": title_el.get("href", ""),
                            "apply_url": title_el.get("href", ""),
                            "description": snippet_el.get_text(strip=True) if snippet_el else "",
                        })
        except Exception as e:
            print(f"Search error: {e}")
        
        return jobs


class JobScraperAgent:
    """
    Multi-agent scraper that uses Firecrawl + fallback + browser.
    Handles CAPTCHAs and login pages gracefully.
    """
    
    def __init__(self):
        self.firecrawl = FirecrawlClient()
        self.http_scraper = HTTPScraper()
        self.captcha_count = 0
    
    async def search_jobs(
        self,
        keywords: List[str],
        locations: List[str],
        max_results: int = 20
    ) -> List[Dict]:
        """Search for jobs using multiple methods."""
        
        jobs = []
        query = " ".join(keywords)
        location = " ".join(locations)
        
        # Method 1: Try Firecrawl search (best for web search)
        print("Trying Firecrawl search...", flush=True)
        firecrawl_results = await self.firecrawl.search(
            f"{query} jobs {location}",
            limit=max_results
        )
        
        if firecrawl_results:
            for r in firecrawl_results:
                jobs.append({
                    "title": r.get("title", ""),
                    "company": r.get("publisher", ""),
                    "location": location,
                    "source": "firecrawl",
                    "source_url": r.get("url", ""),
                    "apply_url": r.get("url", ""),
                    "description": r.get("description", ""),
                })
            print(f"Firecrawl found {len(firecrawl_results)} jobs", flush=True)
        
        # Method 2: Fallback to browser scraper if no results
        if not jobs:
            print("Falling back to browser scraper...", flush=True)
            from agents.job_discovery.discovery import JobDiscoveryAgent
            discovery = JobDiscoveryAgent()
            jobs = await discovery.search_jobs(keywords, locations, max_results)
        
        # Deduplicate
        seen = set()
        unique = []
        for job in jobs:
            url = job.get("source_url") or job.get("apply_url")
            if url and url not in seen:
                seen.add(url)
                unique.append(job)
        
        return unique[:max_results]
    
    def handle_captcha(self, page_content: str) -> bool:
        """Detect and handle CAPTCHA."""
        captcha_indicators = [
            "captcha", "robot", "verify you're human",
            "blocked", "unusual traffic", "Access denied"
        ]
        
        content_lower = page_content.lower()
        for indicator in captcha_indicators:
            if indicator in content_lower:
                self.captcha_count += 1
                print(f"CAPTCHA detected ({self.captcha_count} times)", flush=True)
                return True
        
        return False