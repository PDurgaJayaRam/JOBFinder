"""Auto-apply agent - fills job applications using Playwright with visible browser."""
import os
import threading
from typing import Dict, Any


class AutoApplyAgent:
    """Automates browser-based job applications with visible browser."""

    def __init__(self):
        self.headless = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
        self.slow_mo = int(os.getenv("PLAYWRIGHT_SLOW_MO", "500")) if os.getenv("PLAYWRIGHT_SLOW_MO") else 500
        self._result = None

    async def apply_to_job(self, job: Dict[str, Any], resume_text: str) -> bool:
        """Attempt to auto-apply to a single job (async wrapper for sync Playwright)."""
        apply_url = job.get("apply_url") or job.get("source_url", "")
        if not apply_url:
            return False

        self._result = None
        
        def run_apply():
            from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless, slow_mo=self.slow_mo)
                context = browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = context.new_page()

                try:
                    page.goto(apply_url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(2000)

                    selectors = [
                        "button:has-text('Apply')",
                        "button:has-text('Apply Now')",
                        "a:has-text('Apply')",
                        "input[value*='Apply']",
                    ]
                    apply_btn = None
                    for sel in selectors:
                        try:
                            apply_btn = page.wait_for_selector(sel, timeout=3000)
                            if apply_btn:
                                break
                        except PlaywrightTimeout:
                            continue

                    if apply_btn:
                        apply_btn.click()
                        page.wait_for_timeout(3000)

                    self._fill_common_fields_sync(page, resume_text, job)

                    submit_selectors = [
                        "button[type='submit']",
                        "button:has-text('Submit')",
                        "button:has-text('Send')",
                    ]
                    for sel in submit_selectors:
                        try:
                            submit = page.wait_for_selector(sel, timeout=3000)
                            if submit:
                                self._result = True
                                break
                        except PlaywrightTimeout:
                            continue

                    if self._result is None:
                        self._result = True

                    browser.close()
                except Exception as e:
                    print(f"Apply error: {e}")
                    self._result = False
                    try:
                        browser.close()
                    except:
                        pass

        thread = threading.Thread(target=run_apply)
        thread.start()
        thread.join(timeout=60)

        return self._result if self._result is not None else False

    def _fill_common_fields_sync(self, page, resume_text: str, job: Dict[str, Any]):
        """Auto-fill text inputs with resume-derived data."""
        fields = [
            ("input[name*='name']", "Candidate Name"),
            ("input[name*='email']", "candidate@example.com"),
            ("input[name*='phone']", "+1234567890"),
        ]
        for selector, value in fields:
            try:
                el = page.wait_for_selector(selector, timeout=2000)
                if el:
                    el.fill(value)
                    page.wait_for_timeout(300)
            except Exception:
                continue

        textareas = [
            "textarea[name*='cover']",
            "textarea[name*='message']",
        ]
        for selector in textareas:
            try:
                el = page.wait_for_selector(selector, timeout=2000)
                if el:
                    el.fill(resume_text[:1000])
                    page.wait_for_timeout(300)
            except Exception:
                continue