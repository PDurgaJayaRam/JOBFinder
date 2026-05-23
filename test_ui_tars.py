"""Test UI-TARS agent - autonomous task completion."""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.browser_agent.browser_controller import BrowserController
from agents.vision_scraper.ui_tars_agent import UITarsAgent


async def main():
    """Test UI-TARS with autonomous task."""
    browser = BrowserController(headless=False)
    try:
        await browser.start()
        
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        agent = UITarsAgent(browser, mistral_api_key, max_steps=20)
        
        # Task: Open YouTube, search for video, click to play
        task = "Open YouTube, search for 'sao paulo song', and click on the first video to play it"
        
        print(f"Task: {task}")
        result = await agent.run(task, start_url="https://www.youtube.com")
        
        print(f"\nResult: {result['status']}")
        print(f"Steps: {result.get('steps', 0)}")
    finally:
        print("Closing browser...")
        await browser.close()
        print("Browser closed.")


if __name__ == "__main__":
    asyncio.run(main())
