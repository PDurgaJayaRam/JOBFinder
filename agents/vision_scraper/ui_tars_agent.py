"""UI-TARS Agent - General purpose autonomous agent like UI-TARS Desktop."""

import os
import re
import time
import json
import base64
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Official UI-TARS prompt template
UI_TARS_SYSTEM_PROMPT = """You are a GUI agent. You are given a task and your action history, with screenshots. You need to perform the next action to complete the task.

## Output Format

Thought: ...
Action: ...

## Action Space

click(point='<point>x1 y1</point>')
type(content='xxx')
scroll(direction='down')
wait()
hotkey(key='enter')
finished()

## Note

- Use English in Thought part.
- Write a small plan and finally summarize your next action in one sentence in Thought part.
- If you see a popup/cookie banner, click the close button or 'Accept' first.
- If you see a search box, type the query into it then click the search button.
- If the task is completed, return finished().
- DO NOT use markdown code blocks. Output plain text only."""


class UITarsAgent:
    """UI-TARS autonomous agent - works like UI-TARS Desktop.
    
    Usage:
        agent = UITarsAgent(browser, mistral_api_key)
        result = await agent.run("Open YouTube and search for 'sao paulo song'")
    """

    def __init__(
        self,
        browser_controller,
        mistral_api_key: str,
        model: str = "ministral-14b-latest",
        max_steps: int = 25,
    ):
        self.browser = browser_controller
        self.mistral_api_key = mistral_api_key
        self.model = model
        self.max_steps = max_steps
        self._history: List[Dict] = []
        self._viewport_width = 1400
        self._viewport_height = 900

    def _call_mistral(self, screenshot_b64: str, task: str, history_text: str) -> str:
        """Call Mistral vision model with UI-TARS prompt."""
        import requests
        
        user_content = f"Task: {task}"
        if history_text:
            user_content += f"\n\nAction History:\n{history_text}"
        
        messages = [
            {
                "role": "system",
                "content": UI_TARS_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_content},
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{screenshot_b64}",
                    },
                ],
            }
        ]
        
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.mistral_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.0,
            },
            timeout=60,
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Mistral API error: {response.status_code} - {response.text}")

    def _clean_response(self, text: str) -> str:
        """Remove markdown code blocks and clean response."""
        # Remove markdown code blocks
        text = re.sub(r'```\w*\n', '', text)
        text = text.replace('```', '')
        return text.strip()

    def _parse_action(self, response_text: str) -> Dict[str, Any]:
        """Parse UI-TARS action response."""
        text = self._clean_response(response_text)
        
        # Extract Thought and Action
        thought_match = re.search(r'Thought:\s*(.+?)(?=Action:|$)', text, re.DOTALL)
        action_match = re.search(r'Action:\s*(.+?)(?:\n|$)', text)
        
        thought = thought_match.group(1).strip() if thought_match else ""
        action = action_match.group(1).strip() if action_match else ""
        
        if not action:
            return {"action_type": "error", "error": "No action found", "thought": thought}
        
        # Parse action type and parameters
        if action.startswith("click("):
            # Extract coordinates: click(point='<point>500 400</point>') or click(point='500 400')
            coord_match = re.search(r"point='[^']*?(\d+)\s+(\d+)[^']*?'", action)
            if coord_match:
                x = int(coord_match.group(1))
                y = int(coord_match.group(2))
                # Normalize to 0-1 scale
                norm_x = x / 1000.0
                norm_y = y / 1000.0
                return {
                    "action_type": "click",
                    "action_inputs": {"start_box": [norm_x, norm_y]},
                    "thought": thought,
                }
        
        elif action.startswith("type("):
            content_match = re.search(r"content='([^']+)'", action)
            if content_match:
                return {
                    "action_type": "type",
                    "action_inputs": {"content": content_match.group(1)},
                    "thought": thought,
                }
        
        elif action.startswith("scroll("):
            dir_match = re.search(r"direction='(\w+)'", action)
            if dir_match:
                return {
                    "action_type": "scroll",
                    "action_inputs": {"direction": dir_match.group(1)},
                    "thought": thought,
                }
        
        elif action.startswith("wait()"):
            return {"action_type": "wait", "thought": thought}
        
        elif action.startswith("finished()") or action.startswith("finished("):
            return {"action_type": "finished", "thought": thought}
        
        elif action.startswith("hotkey("):
            key_match = re.search(r"key='([^']+)'", action)
            if key_match:
                return {
                    "action_type": "hotkey",
                    "action_inputs": {"key": key_match.group(1)},
                    "thought": thought,
                }
        
        return {"action_type": "error", "error": f"Unknown action: {action}", "thought": thought}

    async def _execute_action(self, parsed: Dict[str, Any]) -> bool:
        """Execute parsed action using Playwright (inside browser)."""
        action_type = parsed.get("action_type")
        inputs = parsed.get("action_inputs", {})
        
        try:
            if action_type == "click":
                box = inputs.get("start_box")
                if box and len(box) >= 2:
                    x = int(float(box[0]) * self._viewport_width)
                    y = int(float(box[1]) * self._viewport_height)
                    logger.info(f"CLICK at ({x}, {y})")
                    # Use Playwright mouse (clicks inside browser)
                    await self.browser.page.mouse.click(x, y)
                    await self.browser.wait(1)
                    return True
                
                # Fallback: click center
                x = self._viewport_width // 2
                y = self._viewport_height // 2
                logger.info(f"CLICK fallback at ({x}, {y})")
                await self.browser.page.mouse.click(x, y)
                return True
                
            elif action_type == "type":
                content = inputs.get("content", "")
                # Try to find search box, fallback to keyboard
                try:
                    await self.browser.page.click('#search input, input[type="search"], input[placeholder*="Search"], input[name="q"]', timeout=3000)
                    await self.browser.wait(0.5)
                except:
                    # If no search box found, just type (might be already focused)
                    pass
                # Type content
                await self.browser.page.keyboard.type(content)
                await self.browser.wait(0.5)
                # Press Enter
                await self.browser.page.keyboard.press("Enter")
                logger.info(f"TYPE: {content}")
                return True
                
            elif action_type == "scroll":
                direction = inputs.get("direction", "down")
                amount = 500 if direction == "down" else -500
                await self.browser.page.mouse.wheel(0, amount)
                await self.browser.wait(1)
                logger.info(f"SCROLL {direction}")
                return True
                
            elif action_type == "wait":
                await self.browser.wait(3)
                logger.info("WAIT 3s")
                return True
                
            elif action_type == "finished":
                logger.info("FINISHED")
                return True
                
            elif action_type == "hotkey":
                key = inputs.get("key", "")
                if key == "enter":
                    await self.browser.page.keyboard.press("Enter")
                else:
                    await self.browser.page.keyboard.press(key)
                logger.info(f"HOTKEY: {key}")
                return True
            
            return False
        except Exception as e:
            logger.warning(f"Action execution failed: {e}")
            # Don't crash - just wait and continue
            await self.browser.wait(2)
            return False

    async def run(self, task: str, start_url: str = None) -> Dict[str, Any]:
        """Run autonomous UI-TARS agent on any task.
        
        Args:
            task: Natural language task description
            start_url: Optional starting URL
            
        Returns:
            Dict with status, steps, and action history
        """
        logger.info(f"UI-TARS: Starting task: {task}")
        
        # Navigate to start URL if provided
        if start_url:
            try:
                await self.browser.go_to(start_url)
                await self.browser.wait(3)
            except Exception as e:
                logger.error(f"Failed to navigate to {start_url}: {e}")
                return {"status": "failed", "error": f"Navigation failed: {e}", "steps": 0}
        
        # Get viewport dimensions
        try:
            viewport = self.browser.page.viewport_size
            if viewport:
                self._viewport_width = viewport.get("width", 1400)
                self._viewport_height = viewport.get("height", 900)
        except Exception as e:
            logger.error(f"Failed to get viewport: {e}")
            self._viewport_width = 1400
            self._viewport_height = 900
        
        history_text = ""
        last_action = ""
        same_action_count = 0
        consecutive_errors = 0
        
        for step in range(1, self.max_steps + 1):
            logger.info(f"UI-TARS Step {step}/{self.max_steps}")
            
            # Check if browser is still running
            if self.browser.is_browser_crashed():
                return {"status": "failed", "error": "Browser crashed", "steps": step}
            
            # Take screenshot
            try:
                screenshot = await self.browser.take_screenshot()
                if isinstance(screenshot, str) and screenshot.startswith("screenshot_error"):
                    return {"status": "failed", "error": f"Screenshot failed: {screenshot}", "steps": step}
            except Exception as e:
                logger.error(f"Screenshot failed: {e}")
                consecutive_errors += 1
                if consecutive_errors >= 3:
                    return {"status": "failed", "error": f"Too many errors: {e}", "steps": step}
                await self.browser.wait(2)
                continue
            
            # Convert to base64
            if isinstance(screenshot, bytes):
                screenshot_b64 = base64.b64encode(screenshot).decode("utf-8")
            else:
                screenshot_b64 = screenshot
            
            # Call Mistral vision model
            try:
                response_text = self._call_mistral(screenshot_b64, task, history_text)
                logger.info(f"UI-TARS Response: {response_text[:300]}")
                
                # Parse action
                parsed = self._parse_action(response_text)
                logger.info(f"UI-TARS Parsed: {parsed}")
                
                # Add to history
                self._history.append({
                    "step": step,
                    "response": response_text,
                    "parsed": parsed,
                })
                history_text += f"Step {step}: {response_text}\n"
                
                # Detect loops
                current_action = f"{parsed.get('action_type')}_{json.dumps(parsed.get('action_inputs', {}))}"
                if current_action == last_action:
                    same_action_count += 1
                    if same_action_count >= 3:
                        logger.warning(f"Detected loop! Breaking out...")
                        return {
                            "status": "loop_detected",
                            "steps": step,
                            "history": self._history.copy(),
                        }
                else:
                    same_action_count = 0
                last_action = current_action
                
                # Execute action
                success = await self._execute_action(parsed)
                if not success:
                    logger.warning(f"UI-TARS: Action execution failed at step {step}")
                    consecutive_errors += 1
                    if consecutive_errors >= 5:
                        return {
                            "status": "failed",
                            "error": "Too many consecutive action failures",
                            "steps": step,
                        }
                else:
                    consecutive_errors = 0  # Reset on success
                
                # Check if task is complete
                if parsed.get("action_type") == "finished":
                    return {
                        "status": "success",
                        "steps": step,
                        "history": self._history.copy(),
                    }
                
                # Wait for page to update
                await self.browser.wait(2)
                
            except Exception as e:
                logger.error(f"UI-TARS Step {step} failed: {e}")
                import traceback
                traceback.print_exc()
                consecutive_errors += 1
                if consecutive_errors >= 3:
                    return {"status": "failed", "error": str(e), "steps": step}
                await self.browser.wait(2)
        
        return {
            "status": "timeout",
            "error": f"Max steps ({self.max_steps}) reached",
            "steps": self.max_steps,
            "history": self._history.copy(),
        }
