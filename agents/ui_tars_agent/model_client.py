"""UI-TARS model client - Ollama (local) + Hugging Face API fallback."""
import os
import base64
import json
import logging
from typing import Dict, Any, Optional, List
import httpx

logger = logging.getLogger(__name__)


class UITARSModelClient:
    """Client for UI-TARS model via Ollama or Hugging Face API."""

    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "ui-tars")
        self.hf_api_key = os.getenv("HUGGINGFACE_API_KEY", "")
        self.hf_model = os.getenv("HF_MODEL", "bytedance-research/UI-TARS-7B-DPO")
        self.timeout = 120

    def _encode_image(self, image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode("utf-8")

    async def analyze_screenshot(self, screenshot_bytes: bytes, prompt: str) -> Dict[str, Any]:
        """Analyze screenshot and return action decision."""
        # Try Ollama first (local, free)
        try:
            return await self._call_ollama(screenshot_bytes, prompt)
        except Exception as e:
            logger.warning(f"Ollama failed: {e}, trying Hugging Face API")

        # Fallback to Hugging Face API
        if self.hf_api_key:
            try:
                return await self._call_huggingface(screenshot_bytes, prompt)
            except Exception as e:
                logger.warning(f"Hugging Face failed: {e}")

        raise RuntimeError("All UI-TARS providers failed (Ollama + Hugging Face)")

    async def _call_ollama(self, screenshot_bytes: bytes, prompt: str) -> Dict[str, Any]:
        """Call local Ollama UI-TARS model."""
        image_b64 = self._encode_image(screenshot_bytes)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "images": [image_b64],
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 200,
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            return self._parse_response(result.get("response", ""))

    async def _call_huggingface(self, screenshot_bytes: bytes, prompt: str) -> Dict[str, Any]:
        """Call Hugging Face Inference API."""
        image_b64 = self._encode_image(screenshot_bytes)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"https://api-inference.huggingface.co/models/{self.hf_model}",
                headers={"Authorization": f"Bearer {self.hf_api_key}"},
                json={
                    "inputs": {
                        "image": image_b64,
                        "prompt": prompt,
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            if isinstance(result, list):
                text = result[0].get("generated_text", "")
            else:
                text = result.get("generated_text", "")
            return self._parse_response(text)

    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Parse UI-TARS response into structured action."""
        text = text.strip()

        # Try JSON parsing
        if text.startswith("{"):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass

        # Parse UI-TARS format: "Action: click(x, y)" or "Action: type(x, y) text"
        import re

        # Click pattern
        click_match = re.search(r'click\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', text, re.IGNORECASE)
        if click_match:
            return {
                "action": "click",
                "x": int(click_match.group(1)),
                "y": int(click_match.group(2)),
                "confidence": 0.9,
                "reasoning": text[:200],
            }

        # Type pattern
        type_match = re.search(r'type\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s+(.+)', text, re.IGNORECASE)
        if type_match:
            return {
                "action": "type",
                "x": int(type_match.group(1)),
                "y": int(type_match.group(2)),
                "text": type_match.group(3).strip(),
                "confidence": 0.9,
                "reasoning": text[:200],
            }

        # Scroll pattern
        scroll_match = re.search(r'scroll\s*\(\s*(up|down|left|right)\s*\)', text, re.IGNORECASE)
        if scroll_match:
            return {
                "action": "scroll",
                "direction": scroll_match.group(1).lower(),
                "confidence": 0.9,
                "reasoning": text[:200],
            }

        # Done/goal achieved
        if any(w in text.lower() for w in ["done", "complete", "goal achieved", "search results"]):
            return {
                "action": "done",
                "confidence": 0.9,
                "reasoning": text[:200],
            }

        # Default: return raw text
        return {
            "action": "unknown",
            "raw_text": text[:500],
            "confidence": 0.3,
        }

    def is_available(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            r = httpx.get(f"{self.ollama_url}/api/tags", timeout=5)
            return r.status_code == 200
        except:
            return False
