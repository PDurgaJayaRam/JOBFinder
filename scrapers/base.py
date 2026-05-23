"""Base scraper with rate limiting and ethical scraping practices."""
import asyncio
import random
from typing import Dict, Any
import httpx
from fake_useragent import UserAgent


class BaseScraper:
    """Ethical base scraper with built-in rate limiting."""

    def __init__(self, name: str, delay: float = 2.0):
        self.name = name
        self.delay = delay
        self.ua = UserAgent()
        self.headers = {"User-Agent": self.ua.random}
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self._session: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._session = httpx.AsyncClient(
            headers=self.headers,
            timeout=self.timeout,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session:
            await self._session.aclose()

    async def fetch(self, url: str) -> str:
        if not self._session:
            raise RuntimeError("Scraper must be used as async context manager")
        await asyncio.sleep(self.delay + random.uniform(0, 1))
        resp = await self._session.get(url)
        resp.raise_for_status()
        return resp.text

    def detect_pain_signals(self, text: str) -> list[str]:
        signals = ["excel", "administratie", "handmatig", "overwerk", "manual", "spreadsheet", "data entry"]
        found = [s for s in signals if s.lower() in text.lower()]
        return found
