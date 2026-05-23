"""Browser Controller - CloakBrowser wrapper for AI agent."""
from __future__ import annotations

import os
import sys
import json
import time
import base64
import asyncio
import logging
from typing import List, Dict, Any, Optional
from playwright.async_api import Page, Browser, BrowserContext, async_playwright

# Windows fix: ensure ProactorEventLoop for subprocess support
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

logger = logging.getLogger(__name__)

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

# Lazy import to avoid circular dependency
_models_cache = None
def _get_models():
    global _models_cache
    if _models_cache is None:
        from agents.vision_scraper import models as m
        _models_cache = m
    return _models_cache


class BrowserController:
    """Controls browser for AI agent interaction using CloakBrowser stealth."""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        self._action_log = []

    async def start(self):
        """Launch browser with stealth. Uses CloakBrowser if available, falls back to raw Playwright."""
        try:
            from cloakbrowser import launch_async
            logger.info("Launching CloakBrowser (headless=%s)...", self.headless)
            print(f"[BROWSER] Launching CloakBrowser (headless={self.headless})...", flush=True)
            self.browser = await launch_async(headless=self.headless, humanize=True)
            logger.info("CloakBrowser launched OK")
            print("[BROWSER] CloakBrowser launched OK", flush=True)
        except Exception as e:
            logger.warning("CloakBrowser failed (%s), falling back to raw Playwright", e)
            print(f"[BROWSER] CloakBrowser failed ({e}), falling back to raw Playwright", flush=True)
            pw = await async_playwright().start()
            # Get stealth args if available
            try:
                from cloakbrowser import get_default_stealth_args
                extra_args = get_default_stealth_args()
            except Exception:
                extra_args = [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                ]
            self.browser = await pw.chromium.launch(
                headless=self.headless,
                args=extra_args,
            )
            logger.info("Raw Playwright launched OK")

        self.context = await self.browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="Asia/Kolkata",
        )
        self.page = await self.context.new_page()

    async def close(self):
        """Close browser."""
        if self.browser:
            await self.browser.close()

    async def go_to(self, url: str, timeout: int = 30000) -> str:
        """Navigate to URL with retry logic."""
        for attempt in range(2):
            try:
                if not self.page:
                    return "Navigation failed: Page is None"
                await self.page.goto(url, timeout=timeout, wait_until="domcontentloaded")
                await self.page.wait_for_timeout(1000)
                return f"Navigated to {url}"
            except Exception as e:
                error_msg = str(e)
                if "closed" in error_msg.lower():
                    return f"Navigation failed: Browser closed - {e}"
                if attempt == 0:
                    await self.page.wait_for_timeout(500)
                    continue
                return f"Navigation failed: {e}"

    async def take_screenshot(self, full_page: bool = False, path: str = None) -> str:
        """Take screenshot and return base64 encoded image."""
        try:
            if self.is_browser_crashed():
                return "screenshot_error: Browser is not running"
            screenshot_bytes = await self.page.screenshot(full_page=full_page)
            b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            if path:
                os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
                with open(path, 'wb') as f:
                    f.write(screenshot_bytes)
            return b64
        except Exception as e:
            return f"screenshot_error: {e}"

    async def is_screenshot_error(self, result: str) -> bool:
        """Check if screenshot result is an error."""
        return isinstance(result, str) and result.startswith("screenshot_error:")

    async def get_page_content(self, max_chars: int = 8000) -> str:
        """Get page text content."""
        try:
            content = await self.page.evaluate("""() => {
                const clone = document.body.cloneNode(true);
                const remove = clone.querySelectorAll('script, style, noscript, iframe, svg, img');
                remove.forEach(el => el.remove());
                return clone.innerText;
            }""")
            return content[:max_chars]
        except Exception as e:
            return f"Error getting content: {e}"

    async def get_clickable_elements(self) -> List[Dict[str, str]]:
        """Get list of clickable elements with selectors."""
        try:
            elements = await self.page.evaluate("""() => {
                const clickables = document.querySelectorAll('a, button, [role="button"], input[type="submit"], .close, .dismiss, [aria-label*="close"], [aria-label*="Close"], [aria-label*="dismiss"], [class*="close"], [class*="dismiss"], [class*="popup"], [class*="modal"]');
                const result = [];
                clickables.forEach((el, i) => {
                    if (el.offsetParent !== null) {
                        const text = el.innerText?.trim() || el.getAttribute('aria-label') || el.value || '';
                        const tag = el.tagName.toLowerCase();
                        const classes = el.className || '';
                        const id = el.id || '';
                        let selector = tag;
                        if (id) selector += `#${id}`;
                        else if (classes) selector += `.${classes.split(' ').slice(0, 2).join('.')}`;
                        result.push({
                            index: i,
                            tag: tag,
                            text: text.substring(0, 80),
                            selector: selector,
                            href: el.href || '',
                            visible: true
                        });
                    }
                });
                return result.slice(0, 50);
            }""")
            return elements
        except Exception as e:
            return [{"error": str(e)}]

    async def click_element(self, selector: str) -> str:
        """Click element by selector or text."""
        try:
            try:
                await self.page.click(selector, timeout=5000)
                await self.page.wait_for_timeout(800)
                return f"Clicked selector: {selector}"
            except:
                # Try by text content
                clicked = await self.page.evaluate(f"""() => {{
                    const elements = document.querySelectorAll('a, button, [role="button"], span, div');
                    for (const el of elements) {{
                        if (el.innerText?.trim() === "{selector}" || el.innerText?.trim().includes("{selector}")) {{
                            el.click();
                            return true;
                        }}
                    }}
                    return false;
                }}""")
                await self.page.wait_for_timeout(800)
                if clicked:
                    return f"Clicked element with text: {selector}"
                return f"Element not found: {selector}"
        except Exception as e:
            return f"Click failed: {e}"

    async def click_by_index(self, index: int) -> str:
        """Click element by index from get_clickable_elements."""
        try:
            result = await self.page.evaluate(f"""() => {{
                const clickables = document.querySelectorAll('a, button, [role="button"], input[type="submit"], .close, .dismiss, [aria-label*="close"], [aria-label*="Close"], [class*="close"], [class*="dismiss"]');
                const visible = Array.from(clickables).filter(el => el.offsetParent !== null);
                if (visible[{index}]) {{
                    visible[{index}].click();
                    return 'Clicked element at index {index}';
                }}
                return 'No element at index {index}';
            }}""")
            await self.page.wait_for_timeout(800)
            return result
        except Exception as e:
            return f"Click by index failed: {e}"

    async def type_text(self, selector: str, text: str) -> str:
        """Type text into input field."""
        try:
            await self.page.fill(selector, text)
            return f"Typed '{text}' into {selector}"
        except Exception as e:
            return f"Type failed: {e}"

    async def scroll(self, direction: str = "down", amount: int = 500) -> str:
        """Scroll page."""
        try:
            if direction == "down":
                await self.page.evaluate(f"""() => {{
                    window.scrollBy(0, {amount});
                    // Also try scrolling the main content area for sites with fixed headers
                    const main = document.querySelector('main, .main, #main-content, .search-results-list, .jobs-search-results-list, .job-list');
                    if (main) main.scrollBy(0, {amount});
                }}""")
            elif direction == "up":
                await self.page.evaluate(f"window.scrollBy(0, -{amount})")
            elif direction == "bottom":
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.page.wait_for_timeout(1500)
            return f"Scrolled {direction} by {amount}px"
        except Exception as e:
            return f"Scroll failed: {e}"

    async def wait(self, seconds: int = 2) -> str:
        """Wait for page to load."""
        await self.page.wait_for_timeout(seconds * 1000)
        return f"Waited {seconds} seconds"

    async def extract_jobs(self) -> List[Dict[str, Any]]:
        """Extract job listings from current page using robust multi-strategy approach."""
        try:
            url = await self.get_url()
            source = 'web'
            if 'naukri.com' in url: source = 'naukri'
            elif 'linkedin.com' in url: source = 'linkedin'
            elif 'indeed.co' in url or 'indeed.com' in url: source = 'indeed'
            elif 'cutshort.io' in url: source = 'cutshort'
            elif 'glassdoor.' in url: source = 'glassdoor'
            elif 'foundit.in' in url: source = 'foundit'
            elif 'timesjobs.com' in url: source = 'timesjobs'
            elif 'shine.com' in url: source = 'shine'

            if source == 'naukri':
                return await self._extract_naukri_jobs()
            elif source == 'linkedin':
                return await self._extract_linkedin_jobs()
            elif source == 'indeed':
                return await self._extract_indeed_jobs()
            elif source == 'cutshort':
                return await self._extract_cutshort_jobs()
            elif source == 'foundit':
                return await self._extract_foundit_jobs()
            elif source == 'timesjobs':
                return await self._extract_timesjobs_jobs()
            elif source == 'shine':
                return await self._extract_shine_jobs()
            elif source == 'glassdoor':
                return await self._extract_glassdoor_jobs()

            return await self._extract_generic_jobs()
        except Exception as e:
            print(f"Extract jobs error: {e}")
            return []

    async def _extract_naukri_jobs(self) -> List[Dict[str, Any]]:
        """Extract Naukri jobs - only individual job detail pages, no category/nav links."""
        jobs = await self.page.evaluate(r"""() => {
            const jobs = [];
            const seenUrls = new Set();

            // Only find links that are INDIVIDUAL job detail pages
            // Naukri job URLs look like: /job-listings-<title>-<company>-<location>-<exp>-<id>
            const allLinks = document.querySelectorAll('a[href*="/job-listings-"]');
            for (const link of allLinks) {
                const href = link.href || '';
                if (!href || seenUrls.has(href)) continue;

                // Must be a real job listing URL (contains job-listings- pattern)
                if (!href.includes('/job-listings-')) continue;

                const title = link.innerText?.trim() || '';
                if (!title || title.length < 3 || title.length > 200) continue;

                // Skip obvious non-job titles
                const lower = title.toLowerCase();
                if (lower.includes('view all') || lower.includes('see all') ||
                    lower.includes('search') || lower.includes('login') ||
                    lower.includes('register') || lower.includes('download') ||
                    lower.includes('apply with')) continue;

                seenUrls.add(href);

                // Walk up DOM to find the job card container
                let card = link.closest('div[class*="job"], article, div[class*="tuple"], div[class*="card"], li[class*="job"], section[class*="job"], div[class*="Srp"], div[class*="srp"], div[class*="jobTuple"], div[class*="job-tuple"]');
                if (!card) card = link.parentElement;
                if (!card) card = link.parentElement?.parentElement;
                if (!card) card = link.parentElement?.parentElement?.parentElement;

                let company = '';
                let location = 'Not specified';
                let experience = 'Not specified';
                let salary = 'Not specified';
                let description = '';

                if (card) {
                    const lines = card.innerText?.split('\n').map(l => l.trim()).filter(l => l.length > 0) || [];

                    // Find company name - look for company-like text
                    for (const line of lines) {
                        if (line === title) continue;
                        const lowerLine = line.toLowerCase();
                        // Skip UI elements, metadata, etc.
                        if (line.length < 2 || line.length > 80) continue;
                        if (line.includes('days ago') || line.includes('Apply') || line.includes('Actively') ||
                            line.includes('Posted') || line.includes('saved') || line.includes('bookmark') ||
                            lowerLine.includes('job') || lowerLine.includes('location') ||
                            lowerLine.includes('experience') || lowerLine.includes('salary') ||
                            lowerLine.includes('skills') || lowerLine.includes('description') ||
                            lowerLine.includes('role') || lowerLine.includes('industry') ||
                            lowerLine.includes('education') || lowerLine.includes('apply now') ||
                            lowerLine.includes('view details') || lowerLine.includes(' recruiter') ||
                            lowerLine.match(/^(remote|hybrid|on-site)$/i) ||
                            lowerLine.match(/^\d+/)) continue;
                        // Company names typically: start with capital, contain letters/spaces/dots/&
                        if (/^[A-Z][a-zA-Z\s.&()'\-]+$/.test(line)) {
                            company = line;
                            break;
                        }
                    }

                    // Find location
                    const cityKeywords = ['hyderabad', 'bangalore', 'bengaluru', 'chennai', 'mumbai', 'delhi', 'pune',
                        'kolkata', 'noida', 'gurgaon', 'gurugram', 'kochi', 'vizag', 'visakhapatnam',
                        'telangana', 'andhra pradesh', 'karnataka', 'tamil nadu', 'maharashtra',
                        'india', 'remote', 'work from home', 'ahmedabad', 'jaipur', 'lucknow',
                        'chandigarh', 'coimbatore', 'mangalore', 'mysore', 'thiruvananthapuram'];
                    for (const line of lines) {
                        const lowerLine = line.toLowerCase();
                        if (cityKeywords.some(city => lowerLine.includes(city))) {
                            if (!lowerLine.includes('job') && !lowerLine.includes('salary') &&
                                !lowerLine.includes('experience') && !lowerLine.includes('skills') &&
                                !lowerLine.includes('description') && line.length < 100) {
                                location = line;
                                break;
                            }
                        }
                    }

                    // Find experience
                    for (const line of lines) {
                        if (line.match(/\d[\s-]*[\d+]*\s*y(?:ears?|rs?)/i) ||
                            line.match(/fresher/i) ||
                            line.match(/^0[\s-]*[-–]\s*\d/i)) {
                            experience = line;
                            break;
                        }
                    }

                    // Find salary
                    for (const line of lines) {
                        if (line.includes('\u20b9') || line.match(/lac|lakh|k\/yr|per annum|PA\b/i)) {
                            salary = line;
                            break;
                        }
                    }

                    // Find description
                    for (const line of lines) {
                        if (line.length > 40 && line.length < 400 &&
                            !line.includes('days ago') && !line.toLowerCase().includes('apply') &&
                            !line.toLowerCase().includes('job description') &&
                            !line.toLowerCase().includes('company') &&
                            !line.toLowerCase().includes('skills') &&
                            !line.toLowerCase().includes('experience') &&
                            !line.toLowerCase().includes('salary')) {
                            description = line;
                            break;
                        }
                    }
                }

                jobs.push({
                    title,
                    company: company || 'Unknown',
                    location,
                    source: 'naukri',
                    source_url: href,
                    apply_url: href,
                    salary,
                    description,
                    experience_required: experience
                });
            }

            return jobs;
        }""")

        # Validate and deduplicate
        validated = []
        seen_titles = set()
        for job in jobs:
            title = job.get('title', '').strip()
            if not title or len(title) < 3:
                continue
            # Skip category/navigation garbage
            lower = title.lower().strip()
            if lower in ['jobs', 'search', 'login', 'register', 'download', 'fresher jobs',
                         'engineering jobs', 'internet', 'internship', 'data science jobs'] or \
               lower.startswith('jobs in') or lower.startswith('posted by') or \
               lower.startswith('•') or 'talent cloud' in lower or \
               'product based' in lower or 'product companies' in lower:
                continue
            title_key = lower
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            validated.append(job)

        return validated[:30]

    async def _extract_linkedin_jobs(self) -> List[Dict[str, Any]]:
        """Extract LinkedIn jobs - uses /jobs/view/<id> pattern."""
        jobs = await self.page.evaluate(r"""() => {
            const jobs = [];
            const seenUrls = new Set();
            // LinkedIn uses specific card structures
            const allLinks = document.querySelectorAll('a[href*="/jobs/view/"], a[href*="/job/view/"], a[data-job-id]');
            
            for (const link of allLinks) {
                const href = link.href || '';
                const text = link.innerText?.trim() || '';
                
                if (!href || seenUrls.has(href)) continue;
                if (text.length < 4 || text.length > 150) continue;
                
                // Skip navigation/footer links
                if (text.toLowerCase().includes('sign in') || text.toLowerCase().includes('join now') || 
                    text.toLowerCase().includes('login') || text.toLowerCase().includes('register')) continue;
                
                seenUrls.add(href);
                
                // Try to find job card for context
                let card = link.closest('div[data-job-id], div[class*="job"], article, li');
                let company = '';
                let location = 'Not specified';
                let experience = 'Not specified';
                
                if (card) {
                    const lines = card.innerText?.split('\n').map(l => l.trim()).filter(l => l.length > 0) || [];
                    for (const line of lines) {
                        if (line === text) continue;
                        if (line.length > 2 && line.length < 80 && /^[A-Z][a-zA-Z\s.&()'\-]+$/.test(line)) {
                            company = line;
                            break;
                        }
                    }
                    for (const line of lines) {
                        if (line.toLowerCase().includes('hyderabad') || line.toLowerCase().includes('bangalore') ||
                            line.toLowerCase().includes('chennai') || line.toLowerCase().includes('mumbai') ||
                            line.toLowerCase().includes('delhi') || line.toLowerCase().includes('pune') ||
                            line.toLowerCase().includes('remote') || line.toLowerCase().includes('india')) {
                            location = line;
                            break;
                        }
                    }
                    // Extract experience from card
                    for (const line of lines) {
                        if (line.match(/\d[\s-]*[\d+]*\s*y(?:ears?|rs?)/i) || 
                            line.match(/fresher/i) ||
                            line.match(/^0[\s-]*[-–]\s*\d/i) ||
                            line.match(/\d+\+\s*years?/i)) {
                            experience = line;
                            break;
                        }
                    }
                }
                
                jobs.push({
                    title: text,
                    company: company || 'Unknown',
                    location: location,
                    source: 'linkedin',
                    source_url: href,
                    apply_url: href,
                    salary: 'Not specified',
                    description: '',
                    experience_required: experience
                });
            }
            
            return jobs;
        }""")
        
        # If no jobs found via links, try generic extraction
        if not jobs or len(jobs) == 0:
            return await self._extract_generic_jobs()
        
        validated = []
        seen = set()
        for job in jobs:
            key = job.get('title', '').lower().strip()
            if key and key not in seen:
                seen.add(key)
                validated.append(job)
        return validated[:30]

    async def _extract_indeed_jobs(self) -> List[Dict[str, Any]]:
        """Extract Indeed jobs - uses job listing URL patterns."""
        jobs = await self._extract_with_patterns([
            r'/viewjob\?jk=',
            r'/pagead/',
            r'indeed\.com/rc/clk',
            r'/jobs\?q=',
            r'jk=[a-f0-9]+',
        ], 'indeed')

        # If no jobs found, try generic extraction as fallback
        if not jobs:
            return await self._extract_generic_jobs()
        return jobs

    async def _extract_cutshort_jobs(self) -> List[Dict[str, Any]]:
        """Extract CutShort jobs - uses /jobs/<id>-<slug> pattern."""
        jobs = await self._extract_with_patterns([
            r'/jobs/\d+-',
            r'/jobs/\d+',
        ], 'cutshort')

        # If no jobs found, try generic extraction as fallback
        if not jobs:
            return await self._extract_generic_jobs()
        return jobs

    async def _extract_foundit_jobs(self) -> List[Dict[str, Any]]:
        """Extract Foundit jobs - uses /job-details/ and /srdc/jobs/ patterns."""
        jobs = await self._extract_with_patterns([
            r'/job-details/',
            r'/srdc/jobs/',
            r'/job/\d+',
            r'/jobs/\d+',
        ], 'foundit')

        # If no jobs found, try generic extraction as fallback
        if not jobs:
            return await self._extract_generic_jobs()
        return jobs

    async def _extract_timesjobs_jobs(self) -> List[Dict[str, Any]]:
        """Extract TimesJobs jobs - uses /job-detail/ or /jobs/<keyword>-jobs-<id> pattern."""
        jobs = await self._extract_with_patterns([
            r'/job-detail/',
            r'/jobs/.*-jobs-\d+',
            r'/jobs/\d+',
            r'/job/\d+',
        ], 'timesjobs')

        # If no jobs found, try generic extraction as fallback
        if not jobs:
            return await self._extract_generic_jobs()
        return jobs

    async def _extract_shine_jobs(self) -> List[Dict[str, Any]]:
        """Extract Shine jobs - uses /job-details/ or /job/<id> pattern."""
        # Try specific patterns first
        jobs = await self._extract_with_patterns([
            r'/job-details/',
            r'/job/\d+',
            r'/jobs/\d+',
            r'/job-search/',
        ], 'shine')

        # If no jobs found, try generic extraction as fallback
        if not jobs:
            return await self._extract_generic_jobs()
        return jobs

    async def _extract_glassdoor_jobs(self) -> List[Dict[str, Any]]:
        """Extract Glassdoor jobs - handles login modal and extracts visible jobs."""
        jobs = await self.page.evaluate(r"""() => {
            const jobs = [];
            const seenUrls = new Set();
            // Glassdoor uses specific selectors
            const allLinks = document.querySelectorAll('a[href*="/job-listing/"], a[data-job-listing]');
            
            for (const link of allLinks) {
                const href = link.href || '';
                const text = link.innerText?.trim() || '';
                
                if (!href || seenUrls.has(href)) continue;
                if (text.length < 4 || text.length > 150) continue;
                
                seenUrls.add(href);
                
                // Try to find job card for context
                let card = link.closest('div[class*="job"], div[class*="card"], article, li, section');
                let company = '';
                let location = 'Not specified';
                let experience = 'Not specified';
                let salary = 'Not specified';
                
                if (card) {
                    const lines = card.innerText?.split('\n').map(l => l.trim()).filter(l => l.length > 0) || [];
                    for (const line of lines) {
                        if (line === text) continue;
                        if (line.length > 2 && line.length < 80 && /^[A-Z][a-zA-Z\s.&()'\-]+$/.test(line)) {
                            company = line;
                            break;
                        }
                    }
                    for (const line of lines) {
                        if (line.toLowerCase().includes('hyderabad') || line.toLowerCase().includes('bangalore') ||
                            line.toLowerCase().includes('chennai') || line.toLowerCase().includes('mumbai') ||
                            line.toLowerCase().includes('delhi') || line.toLowerCase().includes('pune') ||
                            line.toLowerCase().includes('remote') || line.toLowerCase().includes('india')) {
                            location = line;
                            break;
                        }
                    }
                    for (const line of lines) {
                        if (line.match(/\d[\s-]*[\d+]*\s*y(?:ears?|rs?)/i) || line.match(/fresher/i)) {
                            experience = line;
                            break;
                        }
                    }
                    for (const line of lines) {
                        if (line.includes('\u20b9') || line.match(/lac|lakh|k\/yr|per annum|PA\b/i)) {
                            salary = line;
                            break;
                        }
                    }
                }
                
                jobs.push({
                    title: text,
                    company: company || 'Unknown',
                    location: location,
                    source: 'glassdoor',
                    source_url: href,
                    apply_url: href,
                    salary: salary,
                    description: '',
                    experience_required: experience
                });
            }
            
            return jobs;
        }""");
        
        validated = []
        seen = set()
        for job in jobs:
            key = job.get('title', '').lower().strip()
            if key and key not in seen:
                seen.add(key)
                validated.append(job)
        return validated[:30]

    async def _extract_with_patterns(self, patterns: List[str], source: str) -> List[Dict[str, Any]]:
        """Extract jobs using regex URL patterns - shared logic for all portals."""
        pattern_js = json.dumps(patterns)
        jobs = await self.page.evaluate(f"""() => {{
            const jobs = [];
            const seenUrls = new Set();
            const patterns = {pattern_js};

            // Find all links and match against job URL patterns
            const allLinks = document.querySelectorAll('a[href]');
            for (const link of allLinks) {{
                const href = link.href || '';
                const text = link.innerText?.trim() || '';

                // Match URL against patterns
                let isJobLink = false;
                for (const pattern of patterns) {{
                    if (new RegExp(pattern).test(href)) {{
                        isJobLink = true;
                        break;
                    }}
                }}
                if (!isJobLink) continue;
                if (seenUrls.has(href)) continue;

                // Title must look like a job title
                if (text.length < 4 || text.length > 150) continue;
                const skipKeywords = ['view all', 'see all', 'search', 'login', 'register',
                    'download', 'apply with', 'post job', 'recruiter', 'talent cloud'];
                const lowerText = text.toLowerCase();
                if (skipKeywords.some(kw => lowerText.includes(kw))) continue;

                // Reject category/suggestion links like "2d Animation Jobs In Chennai"
                if (lowerText.match(/jobs\\s+in\\s+\\w+/i)) continue;
                if (lowerText.match(/^[\\w\\s]+\\s+jobs\\s+in\\s+/i)) continue;

                const jobKeywords = ['developer', 'engineer', 'analyst', 'manager', 'consultant',
                    'architect', 'specialist', 'designer', 'lead', 'senior', 'junior',
                    'intern', 'trainee', 'associate', 'coordinator', 'administrator',
                    'tester', 'qa', 'devops', 'full stack', 'backend', 'frontend',
                    'data', 'ml', 'ai', 'cloud', 'security', 'network', 'system',
                    'product', 'project', 'program', 'business', 'technical',
                    'software', 'hardware', 'mobile', 'web', 'appian', 'java',
                    'python', 'react', 'angular', 'node', 'sql', 'fresher'];
                const hasJobKeyword = jobKeywords.some(kw => lowerText.includes(kw));
                if (!hasJobKeyword) continue;

                seenUrls.add(href);

                // Try to find parent card for context
                let card = link.closest('div[class*="job"], div[class*="card"], article, li, section, div[class*="result"], div[class*="listing"]');
                if (!card) card = link.parentElement;
                if (!card) card = link.parentElement?.parentElement;

                let company = '';
                let location = 'Not specified';
                let experience = 'Not specified';
                let salary = 'Not specified';
                let description = '';

                if (card) {{
                    const lines = card.innerText?.split('\\n').map(l => l.trim()).filter(l => l.length > 0) || [];

                    // Find company name
                    for (const line of lines) {{
                        if (line === text) continue;
                        if (line.length < 2 || line.length > 80) continue;
                        if (/^[A-Z][a-zA-Z\\s.&()\\'\\-]+$/.test(line) &&
                            !line.toLowerCase().includes('job') &&
                            !line.toLowerCase().includes('apply') &&
                            !line.toLowerCase().includes('location')) {{
                            company = line;
                            break;
                        }}
                    }}

                    // Find location
                    const cityKeywords = ['hyderabad', 'bangalore', 'bengaluru', 'chennai', 'mumbai', 'delhi', 'pune',
                        'kolkata', 'noida', 'gurgaon', 'gurugram', 'kochi', 'vizag', 'visakhapatnam',
                        'telangana', 'andhra pradesh', 'karnataka', 'tamil nadu', 'maharashtra',
                        'india', 'remote', 'work from home', 'ahmedabad', 'jaipur', 'lucknow'];
                    for (const line of lines) {{
                        const lowerLine = line.toLowerCase();
                        if (cityKeywords.some(city => lowerLine.includes(city))) {{
                            location = line;
                            break;
                        }}
                    }}

                    // Find experience
                    for (const line of lines) {{
                        if (line.match(/\\d[\\s-]*[\\d+]*\\s*y(?:ears?|rs?)/i) ||
                            line.match(/fresher/i) ||
                            line.match(/^0[\\s-]*[-–]\\s*\\d/i)) {{
                            experience = line;
                            break;
                        }}
                    }}

                    // Find salary
                    for (const line of lines) {{
                        if (line.includes('\\u20b9') || line.match(/lac|lakh|k\\/yr|per annum|PA\\b/i)) {{
                            salary = line;
                            break;
                        }}
                    }}

                    // Find description
                    for (const line of lines) {{
                        if (line.length > 40 && line.length < 400 &&
                            !line.toLowerCase().includes('job') &&
                            !line.toLowerCase().includes('apply') &&
                            !line.toLowerCase().includes('company')) {{
                            description = line;
                            break;
                        }}
                    }}
                }}

                jobs.push({{
                    title: text,
                    company: company || 'Unknown',
                    location: location,
                    source: '{source}',
                    source_url: href,
                    apply_url: href,
                    salary: salary,
                    description: description,
                    experience_required: experience
                }});
            }}

            return jobs;
        }}""")

        # Validate and deduplicate
        validated = []
        seen = set()
        for job in jobs:
            key = job.get('title', '').lower().strip()
            if key and key not in seen:
                seen.add(key)
                validated.append(job)
        return validated[:30]

    async def _extract_generic_jobs(self) -> List[Dict[str, Any]]:
        """Fallback: extract jobs using link-based detection for any site."""
        jobs = await self.page.evaluate(r"""() => {
            const jobs = [];
            const seenUrls = new Set();
            const url = window.location.href;

            let source = 'web';
            if (url.includes('naukri.com')) source = 'naukri';
            else if (url.includes('linkedin.com')) source = 'linkedin';
            else if (url.includes('indeed.co') || url.includes('indeed.com')) source = 'indeed';
            else if (url.includes('cutshort.io')) source = 'cutshort';
            else if (url.includes('glassdoor.')) source = 'glassdoor';
            else if (url.includes('foundit.in')) source = 'foundit';
            else if (url.includes('timesjobs.com')) source = 'timesjobs';
            else if (url.includes('shine.com')) source = 'shine';

            // Portal-specific URL patterns for job detail pages
            const jobUrlPatterns = [
                '/job/', '/jobs/', '/career/', '/position/', '/vacancy/', '/opening/',
                '/job-details', '/jobdetails', '/job-description',
                '/jd/', '/view-job/', '/apply-job/',
                // Cutshort: /jobs/<id>-<slug>
                /\/jobs\/\d+-/,
                // Foundit: /job-details/ or /srdc/jobs/
                /\/job-details\//, /\/srdc\/jobs\//,
                // TimesJobs: /job-detail/ or /jobs/<keyword>-jobs-<id>
                /\/job-detail\//, /\/jobs\/.*-jobs-\d+/,
                // Shine: /job-details/ or /job/
                /\/job-details\//, /\/job\/\d+/,
            ];

            // Find links that look like individual job pages
            const allLinks = document.querySelectorAll('a[href]');
            for (const link of allLinks) {
                const href = link.href || '';
                const text = link.innerText?.trim() || '';

                // Must be a job detail link
                let isJobLink = false;
                for (const pattern of jobUrlPatterns) {
                    if (typeof pattern === 'string') {
                        if (href.includes(pattern)) { isJobLink = true; break; }
                    } else {
                        if (pattern.test(href)) { isJobLink = true; break; }
                    }
                }
                if (!isJobLink) continue;
                if (seenUrls.has(href)) continue;

                // Title must look like a job title
                if (text.length < 4 || text.length > 120) continue;
                const jobKeywords = ['developer', 'engineer', 'analyst', 'manager', 'consultant',
                    'architect', 'specialist', 'designer', 'lead', 'senior', 'junior',
                    'intern', 'trainee', 'associate', 'coordinator', 'administrator',
                    'tester', 'qa', 'devops', 'full stack', 'backend', 'frontend',
                    'data', 'ml', 'ai', 'cloud', 'security', 'network', 'system',
                    'product', 'project', 'program', 'business', 'technical',
                    'software', 'hardware', 'mobile', 'web', 'appian', 'java',
                    'python', 'react', 'angular', 'node', 'sql', 'fresher'];
                const hasJobKeyword = jobKeywords.some(kw => text.toLowerCase().includes(kw));
                if (!hasJobKeyword) continue;

                seenUrls.add(href);

                // Try to find parent card for context
                let card = link.closest('div, article, li, section');
                let company = '';
                let location = '';
                let experience = '';
                let salary = '';

                if (card) {
                    const lines = card.innerText?.split('\n').map(l => l.trim()).filter(l => l.length > 0) || [];
                    for (const line of lines) {
                        if (line === text) continue;
                        if (line.length > 2 && line.length < 80 &&
                            /^[A-Z][a-zA-Z\s.&()'\-]+$/.test(line) &&
                            !line.toLowerCase().includes('job') &&
                            !line.toLowerCase().includes('apply') &&
                            !line.toLowerCase().includes('location')) {
                            company = line;
                            break;
                        }
                    }
                    for (const line of lines) {
                        if (line.toLowerCase().includes('hyderabad') || line.toLowerCase().includes('bangalore') ||
                            line.toLowerCase().includes('chennai') || line.toLowerCase().includes('mumbai') ||
                            line.toLowerCase().includes('delhi') || line.toLowerCase().includes('pune') ||
                            line.toLowerCase().includes('remote')) {
                            location = line;
                            break;
                        }
                    }
                    for (const line of lines) {
                        if (line.match(/\d[\s-]*[\d+]*\s*y(?:ears?|rs?)/i) ||
                            line.match(/fresher/i) ||
                            line.match(/^0[\s-]*[-–]\s*\d/i)) {
                            experience = line;
                            break;
                        }
                    }
                    for (const line of lines) {
                        if (line.includes('\u20b9') || line.match(/lac|lakh|k\/yr|per annum|PA\b/i)) {
                            salary = line;
                            break;
                        }
                    }
                }

                jobs.push({
                    title: text,
                    company: company || 'Unknown',
                    location: location || 'Not specified',
                    source,
                    source_url: href,
                    apply_url: href,
                    salary: salary || 'Not specified',
                    description: '',
                    experience_required: experience || 'Not specified'
                });
            }

            return jobs;
        }""")

        validated = []
        seen = set()
        for job in jobs:
            key = job.get('title', '').lower().strip()
            if key and key not in seen:
                seen.add(key)
                validated.append(job)
        return validated[:30]

    async def get_url(self) -> str:
        """Get current URL."""
        return self.page.url

    def log_action(self, action: str, result: str):
        """Log an action."""
        self._action_log.append({"action": action, "result": result, "time": time.time()})

    def get_action_log(self) -> List[Dict]:
        """Get action log."""
        return self._action_log

    def click_at_coordinates(self, x: int, y: int) -> "ActionResult":
        """Click at screen coordinates using PyAutoGUI."""
        m = _get_models()
        start_time = time.time()
        if not PYAUTOGUI_AVAILABLE:
            return m.ActionResult(
                success=False,
                action_type=m.ActionType.CLICK,
                message="PyAutoGUI not available",
                execution_time_ms=0,
                error="Module not installed",
            )
        try:
            pyautogui.click(x, y)
            time.sleep(0.5)
            execution_time = int((time.time() - start_time) * 1000)
            return m.ActionResult(
                success=True,
                action_type=m.ActionType.CLICK,
                message=f"Clicked at ({x}, {y})",
                execution_time_ms=execution_time,
            )
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return m.ActionResult(
                success=False,
                action_type=m.ActionType.CLICK,
                message=f"Failed to click at ({x}, {y})",
                execution_time_ms=execution_time,
                error=str(e),
            )

    def type_text_at_coordinates(self, x: int, y: int, text: str) -> "ActionResult":
        """Click at coordinates and type text using PyAutoGUI."""
        m = _get_models()
        start_time = time.time()
        if not PYAUTOGUI_AVAILABLE:
            return m.ActionResult(
                success=False,
                action_type=m.ActionType.TYPE,
                message="PyAutoGUI not available",
                execution_time_ms=0,
                error="Module not installed",
            )
        try:
            pyautogui.click(x, y)
            time.sleep(0.3)
            pyautogui.typewrite(text, interval=0.05)
            time.sleep(0.5)
            execution_time = int((time.time() - start_time) * 1000)
            return m.ActionResult(
                success=True,
                action_type=m.ActionType.TYPE,
                message=f"Typed '{text}' at ({x}, {y})",
                execution_time_ms=execution_time,
            )
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return m.ActionResult(
                success=False,
                action_type=m.ActionType.TYPE,
                message=f"Failed to type at ({x}, {y})",
                execution_time_ms=execution_time,
                error=str(e),
            )

    def scroll_page(self, direction: str = "down", amount: int = 500) -> "ActionResult":
        """Scroll page using PyAutoGUI."""
        m = _get_models()
        start_time = time.time()
        if not PYAUTOGUI_AVAILABLE:
            return m.ActionResult(
                success=False,
                action_type=m.ActionType.SCROLL,
                message="PyAutoGUI not available",
                execution_time_ms=0,
                error="Module not installed",
            )
        try:
            if direction == "down":
                pyautogui.scroll(-amount)
            elif direction == "up":
                pyautogui.scroll(amount)
            elif direction == "bottom":
                pyautogui.hotkey("ctrl", "end")
            time.sleep(1.5)
            execution_time = int((time.time() - start_time) * 1000)
            return m.ActionResult(
                success=True,
                action_type=m.ActionType.SCROLL,
                message=f"Scrolled {direction} by {amount}",
                execution_time_ms=execution_time,
            )
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return m.ActionResult(
                success=False,
                action_type=m.ActionType.SCROLL,
                message=f"Failed to scroll {direction}",
                execution_time_ms=execution_time,
                error=str(e),
            )

    async def get_page_state(self) -> "PageState":
        """Get current page state including viewport and popup detection."""
        m = _get_models()
        try:
            url = await self.get_url()
            title = await self.page.title()
            viewport = self.page.viewport_size
            has_popup = await self.page.evaluate("""() => {
                const overlays = document.querySelectorAll(
                    '[class*="popup"], [class*="modal"], [class*="overlay"], ' +
                    '[class*="dialog"], [class*="banner"], [class*="cookie"], ' +
                    '[role="dialog"], [role="alertdialog"]'
                );
                return overlays.length > 0;
            }""")
            popup_type = None
            if has_popup:
                popup_type = await self.page.evaluate("""() => {
                    const popup = document.querySelector(
                        '[class*="cookie"], [class*="banner"]'
                    );
                    if (popup) return 'cookie_banner';
                    const dialog = document.querySelector('[role="dialog"]');
                    if (dialog) return 'dialog';
                    const modal = document.querySelector('[class*="modal"]');
                    if (modal) return 'modal';
                    return 'unknown';
                }""")
            return m.PageState(
                url=url,
                title=title,
                is_loaded=True,
                has_popup=has_popup,
                popup_type=popup_type,
                viewport_width=viewport.get("width", 1400) if viewport else 1400,
                viewport_height=viewport.get("height", 900) if viewport else 900,
            )
        except Exception as e:
            return m.PageState(
                url="",
                title="",
                is_loaded=False,
                has_popup=False,
                viewport_width=1400,
                viewport_height=900,
            )

    def is_browser_crashed(self) -> bool:
        """Check if browser process has crashed or become unresponsive."""
        try:
            if not self.browser or not self.page:
                return True
            return False
        except Exception:
            return True
