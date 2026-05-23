"""Vision Agent for navigation-guided scraping."""

import time
import base64
import logging
from typing import List, Optional
from agents.vision_scraper.models import (
    ActionType,
    ActionDecision,
    NavigationStatus,
    NavigationResult,
    PageState,
)
from agents.vision_scraper.rate_limiter import RateLimiter
from agents.vision_scraper.multi_provider_client import MultiProviderAIClient
from agents.browser_agent.browser_controller import BrowserController

logger = logging.getLogger(__name__)


class VisionAgent:
    """Uses AI vision to navigate job portals and reach search results."""

    def __init__(
        self,
        browser: BrowserController,
        ai_client: MultiProviderAIClient,
        rate_limiter: RateLimiter,
        max_steps: int = 10,
    ):
        self.browser = browser
        self.ai_client = ai_client
        self.rate_limiter = rate_limiter
        self.max_steps = max_steps
        self._action_history: List[ActionDecision] = []

    def _build_navigation_prompt(
        self, goal: str, page_state: PageState, step: int
    ) -> str:
        """Build structured prompt for vision model."""
        return f"""
You are navigating a job portal to reach search results. 

GOAL: {goal}
STEP: {step}/{self.max_steps}
CURRENT URL: {page_state.url}
PAGE TITLE: {page_state.title}
HAS POPUP: {page_state.has_popup}

Available actions:
- CLICK: Click at coordinates (provide x_coordinate, y_coordinate)
- TYPE: Type text at coordinates (provide x_coordinate, y_coordinate, text)
- SCROLL: Scroll page (provide scroll_direction: up/down, scroll_amount: pixels)
- WAIT: Wait for loading (provide wait_duration: seconds)
- GOAL_ACHIEVED: When search results are visible
- ERROR: When navigation cannot proceed

Respond with JSON:
{{
  "action_type": "CLICK|TYPE|SCROLL|WAIT|GOAL_ACHIEVED|ERROR",
  "confidence": 0.0-1.0,
  "reasoning": "Why this action",
  "x_coordinate": number (for CLICK/TYPE),
  "y_coordinate": number (for CLICK/TYPE),
  "text": "string (for TYPE)",
  "scroll_direction": "up|down (for SCROLL)",
  "scroll_amount": number (for SCROLL),
  "wait_duration": number (for WAIT),
  "error_message": "string (for ERROR)"
}}

If you see a popup/cookie banner, click the close button or 'Accept' first.
If you see a search box, TYPE the query into it then CLICK the search button.
If search results are already visible, return GOAL_ACHIEVED.
"""

    async def analyze_screenshot(
        self, screenshot_b64: str, goal: str, page_state: PageState, step: int
    ) -> ActionDecision:
        """Analyze screenshot and return action decision."""
        prompt = self._build_navigation_prompt(goal, page_state, step)
        image_bytes = base64.b64decode(screenshot_b64)
        
        response = self.ai_client.vision_complete(
            image=image_bytes,
            prompt=prompt,
        )
        
        parsed = response.get("parsed", {})
        action = ActionDecision(
            action_type=ActionType(parsed.get("action_type", "ERROR")),
            confidence=parsed.get("confidence", 0.0),
            reasoning=parsed.get("reasoning", ""),
            x_coordinate=parsed.get("x_coordinate"),
            y_coordinate=parsed.get("y_coordinate"),
            text=parsed.get("text"),
            scroll_direction=parsed.get("scroll_direction"),
            scroll_amount=parsed.get("scroll_amount"),
            wait_duration=parsed.get("wait_duration"),
            error_message=parsed.get("error_message"),
        )
        return action

    async def execute_action(self, action: ActionDecision) -> bool:
        """Execute action via browser controller. Returns success status."""
        if action.action_type == ActionType.CLICK:
            result = self.browser.click_at_coordinates(
                action.x_coordinate, action.y_coordinate
            )
            logger.info(f"CLICK at ({action.x_coordinate}, {action.y_coordinate}): {result.success}")
            return result.success
            
        elif action.action_type == ActionType.TYPE:
            result = self.browser.type_text_at_coordinates(
                action.x_coordinate, action.y_coordinate, action.text
            )
            logger.info(f"TYPE '{action.text}' at ({action.x_coordinate}, {action.y_coordinate}): {result.success}")
            return result.success
            
        elif action.action_type == ActionType.SCROLL:
            result = self.browser.scroll_page(
                action.scroll_direction or "down", action.scroll_amount or 500
            )
            logger.info(f"SCROLL {action.scroll_direction}: {result.success}")
            return result.success
            
        elif action.action_type == ActionType.WAIT:
            import asyncio
            await asyncio.sleep(action.wait_duration or 2)
            logger.info(f"WAIT {action.wait_duration}s")
            return True
            
        elif action.action_type == ActionType.GOAL_ACHIEVED:
            logger.info("GOAL_ACHIEVED")
            return True
            
        elif action.action_type == ActionType.ERROR:
            logger.error(f"ERROR: {action.error_message}")
            return False
            
        return False

    async def handle_popup(self) -> bool:
        """Detect and dismiss popups. Returns success status."""
        page_state = await self.browser.get_page_state()
        if not page_state.has_popup:
            return True
            
        screenshot = await self.browser.take_screenshot()
        if isinstance(screenshot, str) and screenshot.startswith("screenshot_error"):
            return False
            
        prompt = """
There is a popup/overlay on this page. Find the close button, 'X', 'Accept', 'Dismiss', or 'Continue' button.
Return JSON with action_type: CLICK and the coordinates of the button to dismiss the popup.
If no dismiss button is visible, return action_type: ERROR.
"""
        try:
            action = await self.analyze_screenshot(screenshot, prompt, page_state, 0)
            if action.action_type == ActionType.CLICK:
                return await self.execute_action(action)
        except Exception as e:
            logger.error(f"Popup handling failed: {e}")
            
        import asyncio
        await asyncio.sleep(1)
        return False

    async def navigate_to_search(
        self, portal_url: str, query: str, location: str = ""
    ) -> NavigationResult:
        """Navigate to search results page for given query."""
        start_time = time.time()
        goal = f"Search for '{query}' jobs in '{location}' on this portal"
        
        logger.info(f"Starting navigation to {portal_url} with goal: {goal}")
        
        await self.browser.go_to(portal_url)
        await self.browser.wait(2)
        
        steps_taken = 0
        screenshots_taken = 0
        
        for step in range(1, self.max_steps + 1):
            steps_taken = step
            
            if self.browser.is_browser_crashed():
                return NavigationResult(
                    portal_url=portal_url,
                    status=NavigationStatus.FAILED,
                    steps_taken=steps_taken,
                    actions=self._action_history.copy(),
                    screenshots_taken=screenshots_taken,
                    time_elapsed_ms=int((time.time() - start_time) * 1000),
                    error_message="Browser crashed",
                )
            
            await self.handle_popup()
            
            screenshot = await self.browser.take_screenshot()
            if isinstance(screenshot, str) and screenshot.startswith("screenshot_error"):
                return NavigationResult(
                    portal_url=portal_url,
                    status=NavigationStatus.FAILED,
                    steps_taken=steps_taken,
                    actions=self._action_history.copy(),
                    screenshots_taken=screenshots_taken,
                    time_elapsed_ms=int((time.time() - start_time) * 1000),
                    error_message=f"Screenshot failed: {screenshot}",
                )
            screenshots_taken += 1
            
            page_state = await self.browser.get_page_state()
            
            try:
                action = await self.analyze_screenshot(screenshot, goal, page_state, step)
                self._action_history.append(action)
                
                success = await self.execute_action(action)
                if not success:
                    return NavigationResult(
                        portal_url=portal_url,
                        status=NavigationStatus.FAILED,
                        steps_taken=steps_taken,
                        actions=self._action_history.copy(),
                        screenshots_taken=screenshots_taken,
                        time_elapsed_ms=int((time.time() - start_time) * 1000),
                        error_message=f"Action failed: {action.reasoning}",
                    )
                
                if action.action_type == ActionType.GOAL_ACHIEVED:
                    return NavigationResult(
                        portal_url=portal_url,
                        status=NavigationStatus.SUCCESS,
                        steps_taken=steps_taken,
                        actions=self._action_history.copy(),
                        screenshots_taken=screenshots_taken,
                        time_elapsed_ms=int((time.time() - start_time) * 1000),
                    )
                
                if action.action_type == ActionType.ERROR:
                    return NavigationResult(
                        portal_url=portal_url,
                        status=NavigationStatus.FAILED,
                        steps_taken=steps_taken,
                        actions=self._action_history.copy(),
                        screenshots_taken=screenshots_taken,
                        time_elapsed_ms=int((time.time() - start_time) * 1000),
                        error_message=action.error_message,
                    )
                
                await self.browser.wait(1)
                
            except Exception as e:
                logger.error(f"Navigation step {step} failed: {e}")
                return NavigationResult(
                    portal_url=portal_url,
                    status=NavigationStatus.FAILED,
                    steps_taken=steps_taken,
                    actions=self._action_history.copy(),
                    screenshots_taken=screenshots_taken,
                    time_elapsed_ms=int((time.time() - start_time) * 1000),
                    error_message=str(e),
                )
        
        return NavigationResult(
            portal_url=portal_url,
            status=NavigationStatus.TIMEOUT,
            steps_taken=steps_taken,
            actions=self._action_history.copy(),
            screenshots_taken=screenshots_taken,
            time_elapsed_ms=int((time.time() - start_time) * 1000),
            error_message=f"Max steps ({self.max_steps}) reached",
        )
