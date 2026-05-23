"""Autonomous Browser Agent - Efficient job search with Mistral + DOM extraction.

Architecture:
  Step 3.5 (Brain) = Planning, keywords, matching, scoring
  Mistral (Eyes) = Visual interaction ONLY (click filters, scroll, select jobs)
  DOM Extraction = Fast data extraction (job details from HTML)

Efficient Flow:
  1. Brain creates plan (keywords, experience level, portals)
  2. Navigate to portal, search with keywords
  3. Mistral clicks experience filter (0 years/fresher)
  4. DOM extracts job listings (fast, no API cost)
  5. Mistral clicks on each job to open details
  6. DOM extracts full job details from detail page
  7. Repeat for next portal
"""
import json
import re
import time
import asyncio
from typing import List, Dict, Any, Optional
from ai.ai_client import get_ai_client
from agents.browser_agent.browser_controller import BrowserController


class AutonomousAgent:
    """Efficient job search agent - Mistral for UI, DOM for data."""

    def __init__(self, headless: bool = False):
        self.ai = get_ai_client()
        self.browser = BrowserController(headless=headless)
        self._log_entries = []
        self._brain_context = {}

    def _log(self, message: str):
        self._log_entries.append(message)
        print(f"[AGENT] {message}", flush=True)

    async def _mistral_action(self, instruction: str, screenshot_b64: str = None) -> Dict:
        """Ask Mistral to perform a visual action (click, scroll, select)."""
        try:
            prompt = f"""You are a browser automation agent. Execute this action:

INSTRUCTION: {instruction}

Current URL: {self.browser.page.url if self.browser.page else 'unknown'}

Respond with ONLY a JSON object:
{{
  "action": "click|scroll|select|type|wait|done",
  "target": "What to click/select (text, label, or description)",
  "value": "Value to type or select (if applicable)",
  "success": true/false,
  "message": "What you did or why it failed"
}}"""

            messages = [
                {"role": "system", "content": "You are a browser automation agent. Respond with JSON only."},
                {"role": "user", "content": prompt}
            ]

            # Add screenshot if provided
            if screenshot_b64:
                messages[1]["content"] = [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}}
                ]

            response = await self.ai.chat_completion(
                messages=messages,
                model="mistralai/mistral-large-3-675b-instruct-2512",
                temperature=0.1,
                max_tokens=200,
            )

            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())

        except Exception as e:
            self._log(f"Mistral action error: {e}")

        return {"action": "wait", "success": False, "message": "Could not process"}

    async def _click_element(self, selectors: List[str], timeout: int = 3000) -> bool:
        """Try to click an element using multiple selectors."""
        for selector in selectors:
            try:
                await self.browser.page.click(selector, timeout=timeout)
                self._log(f"Clicked: {selector}")
                return True
            except:
                continue
        return False

    async def _select_experience_filter(self, portal: str, experience: str) -> bool:
        """Select experience filter using DOM analysis - find filter elements in HTML."""
        self._log(f"Selecting experience filter on {portal}")

        # Use JavaScript to find and click experience filter
        result = await self.browser.page.evaluate("""() => {
            const results = {clicked: false, method: '', details: ''};

            // Find all elements that might be experience filters
            const allElements = document.querySelectorAll('*');
            const experienceElements = [];

            for (const el of allElements) {
                const text = (el.innerText || '').toLowerCase().trim();
                const ariaLabel = (el.getAttribute('aria-label') || '').toLowerCase();
                const placeholder = (el.getAttribute('placeholder') || '').toLowerCase();
                const name = (el.getAttribute('name') || '').toLowerCase();
                const id = (el.id || '').toLowerCase();
                const className = (el.className || '').toLowerCase();

                // Check if element is related to experience
                const isExperience = text.includes('experience') || ariaLabel.includes('experience') ||
                                   placeholder.includes('experience') || name.includes('experience') ||
                                   id.includes('experience') || className.includes('experience') ||
                                   text.includes('exp ') || text.includes('exp.');

                if (isExperience && el.offsetParent !== null) {
                    experienceElements.push({
                        tag: el.tagName,
                        text: text.substring(0, 50),
                        type: el.type || '',
                        role: el.getAttribute('role') || '',
                        className: className.substring(0, 100),
                        isClickable: el.tagName === 'BUTTON' || el.tagName === 'A' || el.tagName === 'SELECT' ||
                                    el.getAttribute('role') === 'button' || el.onclick !== null ||
                                    className.includes('btn') || className.includes('button') || className.includes('dropdown') || className.includes('select')
                    });
                }
            }

            // Try to click the most likely experience filter element
            for (const el of experienceElements) {
                if (el.isClickable) {
                    // Find the actual element and click it
                    const selector = el.tag.toLowerCase() +
                        (el.text ? `:contains("${el.text.substring(0, 20)}")` : '');

                    // Try to click using different methods
                    try {
                        // Method 1: Find by text content
                        const elements = document.querySelectorAll('*');
                        for (const elem of elements) {
                            if (elem.innerText && elem.innerText.toLowerCase().includes('experience') &&
                                elem.offsetParent !== null &&
                                (elem.tagName === 'BUTTON' || elem.tagName === 'DIV' || elem.tagName === 'SPAN' ||
                                 elem.tagName === 'A' || elem.tagName === 'LABEL')) {
                                elem.click();
                                results.clicked = true;
                                results.method = 'text click';
                                results.details = `Clicked: ${elem.tagName} with text "${elem.innerText.substring(0, 30)}"`;
                                return results;
                            }
                        }
                    } catch(e) {}
                }
            }

            // If no clickable element found, try dropdowns/selects
            const selects = document.querySelectorAll('select');
            for (const select of selects) {
                const options = select.querySelectorAll('option');
                for (const option of options) {
                    if (option.text.toLowerCase().includes('experience') ||
                        option.value.toLowerCase().includes('experience')) {
                        select.value = option.value;
                        select.dispatchEvent(new Event('change', {bubbles: true}));
                        results.clicked = true;
                        results.method = 'select change';
                        results.details = `Selected: ${option.text}`;
                        return results;
                    }
                }
            }

            results.details = `Found ${experienceElements.length} experience elements`;
            return results;
        }""")

        self._log(f"Filter result: {result}")

        if result.get("clicked"):
            await self.browser.wait(2)

            # Now try to select "Fresher" or "0-1 years"
            fresher_selected = await self.browser.page.evaluate("""() => {
                const results = {selected: false, method: '', details: ''};

                // Look for fresher/0-1 years options
                const fresherTexts = ['fresher', '0-1', '0 - 1', 'entry level', 'entry-level', 'less than 1', '0 years', 'fresher/0-1'];

                // Try clicking elements with fresher text
                const allElements = document.querySelectorAll('*');
                for (const el of allElements) {
                    const text = (el.innerText || '').toLowerCase().trim();
                    const value = (el.value || '').toLowerCase();

                    if (fresherTexts.some(ft => text.includes(ft) || value.includes(ft))) {
                        if (el.offsetParent !== null &&
                            (el.tagName === 'LABEL' || el.tagName === 'SPAN' || el.tagName === 'DIV' ||
                             el.tagName === 'LI' || el.tagName === 'A' || el.tagName === 'BUTTON' ||
                             el.tagName === 'OPTION')) {
                            el.click();
                            results.selected = true;
                            results.method = 'click';
                            results.details = `Clicked: ${el.tagName} with text "${text.substring(0, 30)}"`;
                            return results;
                        }
                    }
                }

                // Try checkbox/radio inputs
                const inputs = document.querySelectorAll('input[type="checkbox"], input[type="radio"]');
                for (const input of inputs) {
                    const label = input.labels?.[0]?.innerText?.toLowerCase() || '';
                    const value = input.value.toLowerCase();

                    if (fresherTexts.some(ft => label.includes(ft) || value.includes(ft))) {
                        input.click();
                        results.selected = true;
                        results.method = 'input click';
                        results.details = `Clicked input: ${label || value}`;
                        return results;
                    }
                }

                results.details = 'No fresher option found';
                return results;
            }""")

            self._log(f"Fresher selection: {fresher_selected}")

            if fresher_selected.get("selected"):
                self._log(f"Selected fresher option: {fresher_selected.get('details')}")
                await self.browser.wait(1)
                return True

        # If DOM approach failed, try Playwright selectors
        try:
            # Common experience filter selectors
            filter_selectors = [
                "text=Experience",
                "text=experience",
                "[aria-label*='experience' i]",
                "[data-testid*='experience' i]",
                "button:has-text('Experience')",
                "div:has-text('Experience'):not(:has(div:has-text('Experience')))",
            ]

            for selector in filter_selectors:
                try:
                    await self.browser.page.click(selector, timeout=2000)
                    self._log(f"Clicked filter via Playwright: {selector}")
                    await self.browser.wait(1)

                    # Try to select fresher option
                    fresher_selectors = [
                        "text=Fresher",
                        "text=0-1 Yrs",
                        "text=Entry Level",
                        "text=0 Years",
                        "text=Less than 1 year",
                        "text=0-1 years",
                    ]

                    for option in fresher_selectors:
                        try:
                            await self.browser.page.click(option, timeout=1500)
                            self._log(f"Selected option via Playwright: {option}")
                            await self.browser.wait(1)
                            return True
                        except:
                            continue

                except:
                    continue

        except Exception as e:
            self._log(f"Playwright filter error: {e}")

        self._log("Could not apply experience filter via DOM or Playwright")
        return False

    async def _extract_jobs_from_listing(self) -> List[Dict]:
        """Extract job listings from current page using DOM (fast, no API cost)."""
        try:
            jobs = await self.browser.extract_jobs()
            if jobs:
                self._log(f"DOM extracted {len(jobs)} jobs from listing")
                return jobs
        except Exception as e:
            self._log(f"DOM extraction error: {e}")

        return []

    async def _open_job_and_extract(self, job_url: str) -> Dict:
        """Open a job page and extract details using DOM (fast)."""
        try:
            # Open in new tab
            new_page = await self.browser.context.new_page()
            await new_page.goto(job_url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(1.5)

            # Extract using DOM
            job_data = await new_page.evaluate("""() => {
                const data = {
                    title: '',
                    company: '',
                    location: '',
                    description: '',
                    requirements: [],
                    skills: [],
                    experience: '',
                    salary: '',
                    apply_url: window.location.href
                };

                // Get title
                const titleEl = document.querySelector('h1, [class*="job-title"], [class*="jobTitle"], [data-testid="job-title"]');
                if (titleEl) data.title = titleEl.innerText.trim();

                // Get company
                const companyEl = document.querySelector('[class*="company"], [class*="employer"], [data-testid="company-name"]');
                if (companyEl) data.company = companyEl.innerText.trim();

                // Get location
                const locationEl = document.querySelector('[class*="location"], [data-testid="location"]');
                if (locationEl) data.location = locationEl.innerText.trim();

                // Get description
                const descEl = document.querySelector('[class*="description"], [class*="job-description"], [class*="jobDescription"], [data-testid="job-description"]');
                if (descEl) data.description = descEl.innerText.trim();

                // Get salary
                const salaryEl = document.querySelector('[class*="salary"], [data-testid="salary"]');
                if (salaryEl) data.salary = salaryEl.innerText.trim();

                // Get experience
                const expEl = document.querySelector('[class*="experience"], [data-testid="experience"]');
                if (expEl) data.experience = expEl.innerText.trim();

                // Extract skills from description
                if (data.description) {
                    const skillPatterns = /(?:java|python|javascript|react|angular|node|sql|html|css|aws|docker|git|spring|django|flask|fastapi|typescript|vue|mongodb|postgresql|redis|kubernetes)/gi;
                    const matches = data.description.match(skillPatterns);
                    if (matches) data.skills = [...new Set(matches.map(s => s.toLowerCase()))];
                }

                return data;
            }""")

            await new_page.close()

            if job_data and job_data.get("title"):
                self._log(f"Extracted job: {job_data.get('title', 'Unknown')}")
                return job_data

        except Exception as e:
            self._log(f"Job detail extraction error: {e}")

        return {}

    async def _scroll_and_extract(self, max_scrolls: int = 3) -> List[Dict]:
        """Scroll page and extract jobs at each position."""
        all_jobs = []

        for i in range(max_scrolls):
            # Extract from current position
            jobs = await self._extract_jobs_from_listing()
            for job in jobs:
                if not any(j.get("title") == job.get("title") and j.get("company") == job.get("company") for j in all_jobs):
                    all_jobs.append(job)

            # Scroll down
            await self.browser.scroll("down", 800)
            await self.browser.wait(1)

        return all_jobs

    async def run_task(self, task: str, target_count: int = 20, keywords: str = "",
                       is_fresher: bool = False, location: str = "Hyderabad",
                       portals: List[str] = None, is_us: bool = False) -> List[Dict]:
        """Run efficient job search using Mistral for UI, DOM for data."""
        self._log(f"Starting efficient job search")
        self._log(f"Keywords: {keywords}, Location: {location}, Fresher: {is_fresher}, Target: {target_count}")

        self._log(f"Launching browser (headless={self.browser.headless})...")
        try:
            await asyncio.wait_for(self.browser.start(), timeout=30)
            self._log(f"Browser launched successfully")
        except asyncio.TimeoutError:
            self._log(f"ERROR: Browser launch timed out after 30s")
            return []
        except Exception as e:
            self._log(f"ERROR: Browser launch failed: {type(e).__name__}: {e}")
            return []
        all_jobs = []
        seen_urls = set()
        portals_to_search = portals or ["naukri", "indeed", "linkedin"]

        try:
            for portal in portals_to_search:
                if len(all_jobs) >= target_count:
                    break

                self._log(f"\n{'='*50}")
                self._log(f"Searching: {portal}")
                self._log(f"{'='*50}")

                # 1. Navigate to portal
                search_url = self._build_search_url(portal, keywords, location)
                self._log(f"Navigating: {search_url}")

                try:
                    await self.browser.go_to(search_url, timeout=30000)
                    await self.browser.wait(2)
                    # Check if page loaded correctly
                    page_url = await self.browser.get_url()
                    page_title = await self.browser.page.title()
                    self._log(f"Page loaded: {page_title[:60]} | URL: {page_url[:80]}")
                except Exception as e:
                    self._log(f"Navigation failed: {e}")
                    continue

                # 2. Close popups
                await self._close_popups()

                # 3. Select experience filter (fresher/0 years) using Mistral
                if is_fresher:
                    await self._select_experience_filter(portal, "0 years/fresher")
                    await self.browser.wait(2)

                # 4. Extract jobs from listing page (DOM - fast)
                listing_jobs = await self._scroll_and_extract(max_scrolls=3)
                self._log(f"Found {len(listing_jobs)} jobs on listing page")
                if listing_jobs:
                    for j in listing_jobs[:3]:
                        self._log(f"  Sample: {j.get('title', 'no-title')} at {j.get('company', 'no-company')}")

                # 5. Open each job page for detailed extraction (DOM - fast)
                for job in listing_jobs[:10]:  # Limit to 10 jobs per portal
                    if len(all_jobs) >= target_count:
                        break

                    job_url = job.get("source_url") or job.get("apply_url")
                    if not job_url or job_url in seen_urls:
                        continue

                    seen_urls.add(job_url)

                    # Extract detailed info from job page
                    detailed_job = await self._open_job_and_extract(job_url)
                    if detailed_job and detailed_job.get("title"):
                        detailed_job["source"] = portal
                        all_jobs.append(detailed_job)
                        self._log(f"Job {len(all_jobs)}: {detailed_job.get('title', 'Unknown')}")
                    elif job.get("title"):
                        # Use listing data if detail extraction fails
                        job["source"] = portal
                        all_jobs.append(job)

                self._log(f"Portal {portal}: {len(all_jobs)} total jobs")

        except Exception as e:
            self._log(f"Error: {e}")
        finally:
            await self.browser.close()

        # Filter jobs based on experience, relevance, and location
        filtered_jobs = self._filter_jobs(all_jobs, keywords, location, is_fresher)

        self._log(f"\nSearch complete: {len(filtered_jobs)} jobs found (filtered from {len(all_jobs)})")
        return filtered_jobs

    def _filter_jobs(self, jobs: List[Dict], keywords: str, location: str, is_fresher: bool) -> List[Dict]:
        """Filter jobs based on experience, relevance, and location."""
        filtered = []
        location_lower = location.lower()
        keywords_lower = keywords.lower()

        # Tech keywords for relevance filtering
        tech_keywords = ["software", "developer", "engineer", "programming", "coder", "tech", "java", "python",
                        "react", "angular", "node", "backend", "frontend", "full stack", "devops", "cloud",
                        "data", "analyst", "qa", "test", "automation", "database", "sql", "api", "web",
                        "mobile", "app", "application", "iot", "embedded", "cyber", "security", "network"]

        # Non-tech job patterns to reject
        non_tech_patterns = ["teacher", "chemist", "dental", "nurse", "accountant", "marketing", "sales",
                           "hr specialist", "business analyst", "content writer", "graphic designer",
                           "security officer", "receptionist", "admin", "clerk", "peon", "driver",
                           "cook", "cleaner", "housekeeping", "data entry", "typing", "back office"]

        # Location aliases
        city_aliases = {
            "hyderabad": ["hyderabad", "secunderabad", "cyberabad", "hyd"],
            "bangalore": ["bangalore", "bengaluru", "blr"],
            "pune": ["pune", "pimpri", "hinjewadi"],
            "chennai": ["chennai", "madras"],
            "delhi": ["delhi", "new delhi", "ncr", "gurgaon", "noida"],
            "mumbai": ["mumbai", "bombay", "thane"],
        }
        target_aliases = city_aliases.get(location_lower, [location_lower])

        for job in jobs:
            title = (job.get("title", "") or "").lower()
            company = (job.get("company", "") or "").lower()
            desc = (job.get("description", "") or "").lower()
            job_location = (job.get("location", "") or "").lower()
            combined = title + " " + company + " " + desc

            # Skip salary search entries
            if "salary search" in title or "salary search" in desc[:100]:
                continue

            # Skip non-tech jobs
            if any(pattern in title for pattern in non_tech_patterns):
                continue

            # Skip if title is not tech-related (must have at least one tech keyword)
            if not any(kw in combined for kw in tech_keywords):
                continue

            # Location filtering
            if job_location and location_lower:
                # Accept if location matches or is empty/generic
                if not any(alias in job_location for alias in target_aliases):
                    # Skip if location is specified but doesn't match
                    if job_location not in ["", "not specified", "india", "remote"]:
                        continue

            # Experience filtering for freshers
            if is_fresher:
                # Reject senior roles
                senior_patterns = ["senior", "lead", "principal", "staff", "director", "manager",
                                  "architect", "head", "chief", " ii", " iii", " iv", " v",
                                  " l2", " l3", " l4", " l5", " l6", "-ii", "-iii", "-iv"]
                if any(w in title for w in senior_patterns):
                    continue

                # Check experience requirement
                exp = (job.get("experience", "") or "").lower()
                if exp and exp != "not specified" and exp != "not mentioned":
                    # Parse experience range
                    exp_match = re.search(r'(\d+)\s*[-–+]\s*(\d*)', exp)
                    if exp_match:
                        min_exp = int(exp_match.group(1))
                        if min_exp > 2:  # Reject if requires 2+ years
                            continue

                # Check if title indicates fresher-friendly
                fresher_indicators = ["fresher", "junior", "entry level", "intern", "trainee", "graduate", "0-1", "0-2"]
                is_fresher_friendly = any(w in title for w in fresher_indicators)

                # If experience is not specified, only keep if title indicates fresher-friendly
                if (not exp or exp in ["not specified", "not mentioned"]) and not is_fresher_friendly:
                    # Keep jobs without experience if they have matching skills
                    matched_skills = [s for s in ["java", "python", "sql", "html", "css"] if s in combined]
                    if not matched_skills:
                        continue

            filtered.append(job)

        return filtered

    async def _close_popups(self):
        """Close common popups and modals."""
        close_selectors = [
            "button[aria-label='Dismiss']",
            "button[aria-label='Close']",
            "button[aria-label='Reject all']",
            ".modal-close",
            "button:has-text('Got it')",
            "button:has-text('Accept')",
            "button:has-text('Reject')",
            "button:has-text('Close')",
        ]

        for selector in close_selectors:
            try:
                await self.browser.page.click(selector, timeout=1000)
                await asyncio.sleep(0.5)
            except:
                continue

        try:
            await self.browser.page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
        except:
            pass

    def _build_search_url(self, portal: str, keywords: str, location: str) -> str:
        """Build search URL for a portal."""
        kw = keywords.split(",")[0].strip().replace(" ", "%20")
        loc = location.replace(" ", "%20")
        kw_dash = kw.replace("%20", "-")
        loc_dash = loc.replace("%20", "-")

        urls = {
            "naukri": f"https://www.naukri.com/{kw_dash}-jobs-in-{loc_dash}",
            "indeed": f"https://in.indeed.com/jobs?q={kw}&l={loc}",
            "linkedin": f"https://www.linkedin.com/jobs/search/?keywords={kw}&location={loc}",
            "glassdoor": f"https://www.glassdoor.co.in/Job/{loc_dash}-{kw_dash}-jobs-SRCH_IL.0,{len(loc_dash)}.htm",
            "timesjobs": f"https://www.timesjobs.com/candidate/job-search.html?from=submit&actualTxtKeywords={kw}&searchBy=1&fjType=1&jobType=1&locationType=1&location={loc}",
            "shine": f"https://www.shine.com/job-search/{kw_dash}-jobs-in-{loc_dash}",
            "foundit": f"https://www.foundit.in/srp/results?query={kw}&location={loc}",
            "cutshort": f"https://cutshort.io/jobs?q={kw}&location={loc}",
        }

        return urls.get(portal, f"https://www.naukri.com/{kw_dash}-jobs-in-{loc_dash}")
