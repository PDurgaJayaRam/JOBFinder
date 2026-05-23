"""Standalone apply script - opens job application pages in browser."""
import sys
import os
import json
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


async def main():
    data_file = sys.argv[1] if len(sys.argv) > 1 else ""
    headless = sys.argv[2].lower() == "true" if len(sys.argv) > 2 else False

    if not data_file or not os.path.exists(data_file):
        print("[APPLY] No data file found", flush=True)
        return

    with open(data_file) as f:
        data = json.load(f)

    jobs = data.get("jobs", [])
    print(f"[APPLY] Starting: applying to {len(jobs)} jobs", flush=True)

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, slow_mo=100)
        context = await browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        for i, job in enumerate(jobs, 1):
            url = job.get("apply_url", "")
            if not url:
                print(f"[APPLY] [{i}] No apply URL for {job.get('title', 'Unknown')}", flush=True)
                continue

            try:
                print(f"[APPLY] [{i}] Opening: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}", flush=True)
                page = await context.new_page()
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)
                print(f"[APPLY] [{i}] Page loaded — complete the application manually", flush=True)
                await page.wait_for_timeout(5000)
            except Exception as e:
                print(f"[APPLY] [{i}] Error: {e}", flush=True)

        await browser.close()

    print(f"[APPLY] Done — opened {len(jobs)} application pages", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
