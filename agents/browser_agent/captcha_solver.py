"""Free Captcha Solver - Uses stealth techniques and human-like behavior to bypass captchas."""
import os
import re
import time
import asyncio
import random
from typing import Optional, Dict, Any
from playwright.async_api import Page, BrowserContext


class FreeCaptchaSolver:
    """Free captcha solver using stealth techniques and human-like behavior.
    
    This solver uses multiple techniques to bypass captchas without any paid API:
    1. Stealth browser configuration (spoofs automation signals)
    2. Human-like mouse movements and delays
    3. Automatic checkbox clicking for Cloudflare Turnstile
    4. Waiting for auto-resolution (Cloudflare often auto-passes)
    5. Portal skipping for impossible captchas
    """

    def __init__(self):
        self._log_callback = None
        self.solve_attempts = 0
        self.max_solve_time = 20  # Max seconds to try solving

    def set_logger(self, callback):
        self._log_callback = callback

    def _log(self, msg: str):
        if self._log_callback:
            self._log_callback(msg)
        else:
            print(f"[CAPTCHA] {msg}")

    async def add_stealth_to_context(self, context: BrowserContext):
        """Add stealth scripts to browser context to avoid detection."""
        # Remove webdriver property
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)
        
        # Spoof plugins
        await context.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        # Spoof languages
        await context.add_init_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
        
        # Remove cdc_ properties (Playwright detection)
        await context.add_init_script("""
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        # Spoof chrome property
        await context.add_init_script("""
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
        """)

    async def human_like_delay(self, min_ms: int = 500, max_ms: int = 2000):
        """Add human-like random delay."""
        delay = random.uniform(min_ms / 1000, max_ms / 1000)
        await asyncio.sleep(delay)

    async def human_like_click(self, page: Page, selector: str) -> bool:
        """Click with human-like behavior (move mouse, wait, click)."""
        try:
            # Wait for element
            await page.wait_for_selector(selector, timeout=5000)
            
            # Get element position
            position = await page.evaluate(f"""() => {{
                const el = document.querySelector('{selector}');
                if (!el) return null;
                const rect = el.getBoundingClientRect();
                return {{
                    x: rect.left + rect.width / 2 + (Math.random() - 0.5) * 10,
                    y: rect.top + rect.height / 2 + (Math.random() - 0.5) * 10
                }};
            }}""")
            
            if position:
                # Move mouse to position (human-like)
                await page.mouse.move(position['x'], position['y'], steps=random.randint(10, 20))
                await asyncio.sleep(random.uniform(0.1, 0.3))
                
                # Click
                await page.mouse.click(position['x'], position['y'])
                return True
            
            # Fallback to regular click
            await page.click(selector)
            return True
        except:
            return False

    async def detect_captcha_type(self, page: Page) -> Optional[str]:
        """Detect captcha type on current page."""
        try:
            content = await page.content()
            text = await page.evaluate("() => document.body.innerText.toLowerCase()")
            title = await page.title()
            
            # Cloudflare Interstitial
            if any(ind in text for ind in ["verify you are human", "additional verification", "ray id"]) or \
               any(ind in title.lower() for ind in ["just a moment", "attention required"]):
                if "cf-turnstile" in content or "turnstile" in content.lower():
                    return "cloudflare_turnstile"
                return "cloudflare_interstitial"
            
            # Cloudflare Turnstile widget
            if "cf-turnstile" in content:
                return "cloudflare_turnstile"
            
            # reCAPTCHA
            if "g-recaptcha" in content:
                return "recaptcha_v2"
            
            # hCaptcha
            if "h-captcha" in content:
                return "hcaptcha"
            
            return None
        except:
            return None

    async def solve_cloudflare_interstitial(self, page: Page) -> bool:
        """Solve Cloudflare Interstitial using free techniques."""
        self._log("Attempting to solve Cloudflare challenge (free method)...")
        self.solve_attempts += 1
        
        try:
            # Method 1: Wait for auto-resolution (Cloudflare often auto-passes after a few seconds)
            self._log("Waiting for auto-resolution...")
            for i in range(15):  # Wait up to 15 seconds
                await asyncio.sleep(1)
                
                # Check if challenge is gone
                text = await page.evaluate("() => document.body.innerText.toLowerCase()")
                title = await page.title()
                
                if "verify you are human" not in text and \
                   "just a moment" not in title.lower() and \
                   "additional verification" not in text:
                    self._log("Cloudflare challenge passed automatically!")
                    return True
                
                # Method 2: Try clicking the checkbox after 3 seconds
                if i == 3:
                    self._log("Trying to click verification checkbox...")
                    # Try various selectors for the checkbox
                    selectors = [
                        "input[type='checkbox']",
                        "#cf-turnstile input[type='checkbox']",
                        ".cf-turnstile input[type='checkbox']",
                        "[class*='challenge'] input[type='checkbox']",
                        "iframe[src*='challenge'] + input[type='checkbox']",
                    ]
                    
                    for selector in selectors:
                        try:
                            clicked = await self.human_like_click(page, selector)
                            if clicked:
                                self._log("Clicked verification checkbox")
                                await asyncio.sleep(3)
                                break
                        except:
                            continue
                
                # Method 3: Try clicking any "Verify" or "Continue" button
                if i == 8:
                    self._log("Looking for verify/continue button...")
                    try:
                        # Find button by text
                        buttons = await page.evaluate("""() => {
                            const buttons = document.querySelectorAll('button, a, [role="button"]');
                            const results = [];
                            buttons.forEach(btn => {
                                const text = btn.innerText?.toLowerCase() || '';
                                if (text.includes('verify') || text.includes('continue') || 
                                    text.includes('proceed') || text.includes('confirm')) {
                                    results.push(btn.tagName.toLowerCase() + 
                                        (btn.id ? '#' + btn.id : '') + 
                                        (btn.className ? '.' + btn.className.split(' ')[0] : ''));
                                }
                            });
                            return results;
                        }""")
                        
                        for btn_selector in buttons[:3]:
                            try:
                                await self.human_like_click(page, btn_selector)
                                self._log(f"Clicked button: {btn_selector}")
                                await asyncio.sleep(3)
                                break
                            except:
                                continue
                    except:
                        pass
                
                # Method 4: Try clicking the Turnstile widget directly
                if i == 5:
                    self._log("Trying to click Turnstile widget...")
                    try:
                        # Click on the cf-turnstile container
                        await page.click("#cf-turnstile", timeout=3000)
                        self._log("Clicked Turnstile container")
                        await asyncio.sleep(3)
                    except:
                        try:
                            await page.click("[class*='cf-turnstile']", timeout=3000)
                            self._log("Clicked Turnstile by class")
                            await asyncio.sleep(3)
                        except:
                            pass
                
                # Method 5: Reload page (sometimes helps)
                if i == 12:
                    self._log("Reloading page to retry...")
                    await page.reload(wait_until="domcontentloaded")
                    await asyncio.sleep(3)
            
            self._log("Cloudflare challenge not solved after 15s")
            return False
            
        except Exception as e:
            self._log(f"Error solving Cloudflare: {e}")
            return False

    async def solve_recaptcha_free(self, page: Page) -> bool:
        """Try to solve reCAPTCHA by clicking the checkbox."""
        self._log("Attempting to solve reCAPTCHA (free method)...")
        
        try:
            # Wait for reCAPTCHA to load
            await asyncio.sleep(2)
            
            # Click the reCAPTCHA checkbox
            selectors = [
                ".recaptcha-checkbox",
                "#recaptcha-anchor",
                "[role='checkbox']",
                ".g-recaptcha",
            ]
            
            for selector in selectors:
                try:
                    clicked = await self.human_like_click(page, selector)
                    if clicked:
                        self._log(f"Clicked reCAPTCHA checkbox")
                        await asyncio.sleep(5)
                        
                        # Check if solved
                        text = await page.evaluate("() => document.body.innerText.toLowerCase()")
                        if "recaptcha" not in text or "verify" not in text:
                            return True
                except:
                    continue
            
            return False
        except Exception as e:
            self._log(f"Error solving reCAPTCHA: {e}")
            return False

    async def solve(self, page: Page) -> bool:
        """Auto-detect and solve captcha using free methods.
        
        Returns True if captcha was solved, False otherwise.
        """
        captcha_type = await self.detect_captcha_type(page)
        
        if not captcha_type:
            return False
        
        self._log(f"Detected captcha type: {captcha_type}")
        
        if captcha_type in ["cloudflare_interstitial", "cloudflare_turnstile"]:
            return await self.solve_cloudflare_interstitial(page)
        elif captcha_type in ["recaptcha_v2", "recaptcha_v3"]:
            return await self.solve_recaptcha_free(page)
        elif captcha_type == "hcaptcha":
            # hCaptcha is hard to solve without API, skip
            self._log("hCaptcha detected - skipping (requires API)")
            return False
        
        return False

    async def is_page_blocked(self, page: Page) -> bool:
        """Check if page is blocking access (captcha, 403, etc)."""
        try:
            content = await page.content()
            text = await page.evaluate("() => document.body.innerText.toLowerCase()")
            title = await page.title()
            
            indicators = [
                "verify you are human", "cloudflare", "additional verification",
                "ray id", "just a moment", "access denied", "403", "forbidden",
                "blocked", "captcha", "security check", "attention required"
            ]
            return any(ind in text or ind in title.lower() for ind in indicators)
        except:
            return False
