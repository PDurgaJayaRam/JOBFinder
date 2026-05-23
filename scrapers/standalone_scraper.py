"""Standalone Playwright scraper - run via subprocess, no Playwright imports in main process."""
import sys
import json
from playwright.sync_api import sync_playwright


def scrape_jobs():
    query = sys.argv[1] if len(sys.argv) > 1 else "Python"
    location = sys.argv[2] if len(sys.argv) > 2 else "Hyderabad"
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    headless = sys.argv[4].lower() == "true" if len(sys.argv) > 4 else False

    print(f"[SCRAPER] Starting: query={query}, location={location}, limit={limit}, headless={headless}", flush=True)

    jobs = []
    seen_urls = set()
    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=100)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Indeed
        try:
            print("[SCRAPER] Trying Indeed...", flush=True)
            url = f"https://www.indeed.com/jobs?q={query.replace(' ', '+')}&l={location.replace(' ', '+')}"
            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)
            page.wait_for_timeout(3000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

            # Updated selectors for Indeed
            cards = page.query_selector_all("div.job-card-container, div.job_seen_beacon, div[data-testid='job-card']")
            print(f"[SCRAPER] Indeed: found {len(cards)} cards", flush=True)

            for card in cards[:limit]:
                try:
                    # Try multiple selectors
                    title_el = card.query_selector("h2.jobTitle, a.job-title, span[data-testid='job-title'], div.job-title")
                    company_el = card.query_selector("span.companyName, a.companyName, span[data-testid='company-name'], div.company")
                    loc_el = card.query_selector("div.companyLocation, span[data-testid='job-location'], div.location")
                    link_el = card.query_selector("a.jcs-JobTitle, a.job-card-container__link, a[data-testid='job-link']")

                    if not link_el:
                        # Try getting from parent
                        link_el = card.query_selector("a")

                    if title_el and link_el:
                        href = link_el.get_attribute("href") or ""
                        if not href.startswith("http"):
                            href = f"https://www.indeed.com{href}" if href.startswith("/") else f"https://www.indeed.com/{href}"

                        if href and "indeed.com" in href and href not in seen_urls:
                            seen_urls.add(href)
                            title_text = title_el.inner_text().strip()
                            if title_text:
                                jobs.append({
                                    "title": title_text,
                                    "company": company_el.inner_text().strip() if company_el else "Unknown Company",
                                    "location": loc_el.inner_text().strip() if loc_el else location,
                                    "source": "indeed",
                                    "source_url": href,
                                    "apply_url": href,
                                    "salary": "",
                                    "experience_required": "",
                                    "skills_required": [],
                                    "description": "",
                                    "remote": "remote" in title_text.lower(),
                                    "walk_in": "walkin" in title_text.lower(),
                                    "internship": "intern" in title_text.lower(),
                                })
                except Exception as e:
                    errors.append(f"Indeed card error: {e}")
                    continue
            print(f"[SCRAPER] Indeed: extracted {len(jobs)} jobs", flush=True)
        except Exception as e:
            errors.append(f"Indeed error: {e}")
            print(f"[SCRAPER] Indeed failed: {e}", flush=True)

        # Naukri
        try:
            print("[SCRAPER] Trying Naukri...", flush=True)
            url = f"https://www.naukri.com/jobs?q={query.replace(' ', '-')}&l={location.replace(' ', '-')}"
            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)
            page.wait_for_timeout(3000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

            # Updated selectors for Naukri
            cards = page.query_selector_all("article.jobTuple, div.job-card, div.srp-jobtuple-wrapper")
            print(f"[SCRAPER] Naukri: found {len(cards)} cards", flush=True)

            for card in cards[:limit]:
                try:
                    title_el = card.query_selector("a.title, h2.title, a.job-card__title")
                    company_el = card.query_selector("a.subTitle, span.companyInfo, a.companyName")
                    loc_el = card.query_selector("li.location, span.location, div.location")
                    link_el = card.query_selector("a.title, a.jobTupleHeader")

                    if title_el:
                        href = title_el.get_attribute("href") or ""
                        if href and href not in seen_urls:
                            seen_urls.add(href)
                            title_text = title_el.inner_text().strip()
                            if title_text:
                                jobs.append({
                                    "title": title_text,
                                    "company": company_el.inner_text().strip() if company_el else "Unknown Company",
                                    "location": loc_el.inner_text().strip() if loc_el else location,
                                    "source": "naukri",
                                    "source_url": href if href.startswith("http") else f"https://www.naukri.com{href}",
                                    "apply_url": href if href.startswith("http") else f"https://www.naukri.com{href}",
                                    "salary": "",
                                    "experience_required": "",
                                    "skills_required": [],
                                    "description": "",
                                    "remote": "remote" in title_text.lower(),
                                    "walk_in": "walkin" in title_text.lower(),
                                    "internship": "intern" in title_text.lower(),
                                })
                except Exception as e:
                    errors.append(f"Naukri card error: {e}")
                    continue
            print(f"[SCRAPER] Naukri: extracted {len([j for j in jobs if j['source']=='naukri'])} jobs", flush=True)
        except Exception as e:
            errors.append(f"Naukri error: {e}")
            print(f"[SCRAPER] Naukri failed: {e}", flush=True)

        # LinkedIn - often blocks, so we try but don't rely on it
        try:
            print("[SCRAPER] Trying LinkedIn...", flush=True)
            url = f"https://www.linkedin.com/jobs/search?keywords={query.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)
            page.wait_for_timeout(3000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

            # Updated selectors for LinkedIn
            cards = page.query_selector_all("div.base-card, li.job-card-container, div.job-card-list__item")
            print(f"[SCRAPER] LinkedIn: found {len(cards)} cards", flush=True)

            for card in cards[:limit]:
                try:
                    title_el = card.query_selector("h3.base-search-card__title, h3.job-card-list__title")
                    company_el = card.query_selector("a.hidden-nested-link, span.job-card-container__company-name")
                    loc_el = card.query_selector("span.job-search-card__location, span.job-card-container__metadata-item")
                    link_el = card.query_selector("a.base-card__full-link, a.job-card-list__cta")

                    if title_el and link_el:
                        href = link_el.get_attribute("href") or ""
                        if href and href not in seen_urls:
                            seen_urls.add(href)
                            title_text = title_el.inner_text().strip()
                            if title_text:
                                jobs.append({
                                    "title": title_text,
                                    "company": company_el.inner_text().strip() if company_el else "Unknown Company",
                                    "location": loc_el.inner_text().strip() if loc_el else location,
                                    "source": "linkedin",
                                    "source_url": href,
                                    "apply_url": href,
                                    "salary": "",
                                    "experience_required": "",
                                    "skills_required": [],
                                    "description": "",
                                    "remote": "remote" in title_text.lower(),
                                    "walk_in": False,
                                    "internship": "intern" in title_text.lower(),
                                })
                except Exception as e:
                    errors.append(f"LinkedIn card error: {e}")
                    continue
            print(f"[SCRAPER] LinkedIn: extracted {len([j for j in jobs if j['source']=='linkedin'])} jobs", flush=True)
        except Exception as e:
            errors.append(f"LinkedIn error: {e}")
            print(f"[SCRAPER] LinkedIn failed: {e}", flush=True)

        browser.close()

    print(f"[SCRAPER] Total jobs extracted: {len(jobs)}", flush=True)
    if errors:
        print(f"[SCRAPER] Errors: {errors[:5]}", flush=True)

    print(json.dumps(jobs[:limit]))

if __name__ == "__main__":
    scrape_jobs()