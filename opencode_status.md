# Project Status — Job Search AI Agent

**Last Updated:** Wed May 20 2026
**Server:** `http://127.0.0.1:8001`
**Status:** Active development

---

## Architecture Overview

| Component | File | Role |
|-----------|------|------|
| **Brain (Orchestrator)** | `agents/dual_model_orchestrator.py` | Search planning, keyword routing, experience filtering, matching, scoring |
| **Hands (Browser)** | `agents/browser_agent/browser_controller.py` | Portal navigation, popup handling, JS-based job extraction |
| **Job Saver** | `agents/job_saver.py` | DB persistence, deduplication, secondary experience filter, ATS scoring |
| **Frontend UI** | `frontend/public/chat.html` | Resume upload, keyword input, location, experience selector, portal checkboxes, target count |
| **Chat Router** | `agents/chat_agent/agent.py` | Routes messages, passes UI context to orchestrator |

---

## All Updates (Chronological)

### 1. Strict UI-Driven Parameter Passing
- **Problem:** Search used hardcoded defaults instead of live UI selections
- **Fix:** All search parameters (keywords, location, target count, experience level, portals) are read directly from DOM inputs at send time. No cached settings. No fallback defaults except empty strings.

### 2. Removed Default UI Values
- **Problem:** UI pre-filled keywords, pre-checked portals, and set default target count
- **Fix:** Keywords input is empty by default. All portal checkboxes are unchecked. Target count field is empty. User must explicitly set everything.

### 3. Infinite Search Loop Fix
- **Problem:** Search loop repeated portals endlessly, causing browser crashes
- **Fix:** Each selected portal is searched exactly once per keyword cycle. Additional keywords are tried only on the first portal if target count isn't met. Loop terminates when target is reached or portals/keywords are exhausted.

### 4. Portal-Specific JS Extraction
- **Problem:** Generic extraction returned poor results across different portals
- **Fix:** Implemented dedicated extraction methods for each portal:
  - `_extract_naukri_jobs()` — Uses `/job-listings-` URL pattern, card-walking for company/location/experience
  - `_extract_linkedin_jobs()` — Uses `/jobs/view/<id>` pattern, extracts experience from card
  - `_extract_indeed_jobs()` — Uses Indeed-specific selectors
  - `_extract_cutshort_jobs()` — Uses `/jobs/<id>-<slug>` pattern
  - `_extract_foundit_jobs()` — Uses `/job-details/` and `/srdc/jobs/` patterns
  - `_extract_timesjobs_jobs()` — Uses `/job-detail/` and `/jobs/<keyword>-jobs-<id>` patterns
  - `_extract_shine_jobs()` — Uses `/job-details/` and `/job/<id>` patterns
  - `_extract_glassdoor_jobs()` — Uses `/job-listing/` pattern with login modal handling
  - `_extract_generic_jobs()` — Universal fallback with multi-pattern URL matching

### 5. Syntax Error Fixes
- **Problem:** `NameError: name 'context' is not defined` and `re` module import errors
- **Fix:** Added proper imports and variable scoping in orchestrator and browser controller

### 6. JavaScript Leaking into Python (CRITICAL FIX)
- **Problem:** `_extract_linkedin_jobs()` had JavaScript code outside the Python string (lines 469-482): `!jobs`, `jobs.length`, `this._extract_generic_jobs()`, `const validated`, `new Set()`
- **Fix:** Replaced with correct Python: `not jobs`, `len(jobs)`, `self._extract_generic_jobs()`, `validated = []`, `seen = set()`
- **Also:** Removed stray `}` on line 480 that caused `SyntaxError: unmatched '}'`

### 7. Strict Fresher Filter Implementation
- **Problem:** Experienced jobs (Senior, Lead, Manager, Software Engineer II/III) were appearing in fresher results
- **Fix:** Multi-layer filtering in both orchestrator and job_saver:
  - **Title rejection:** Blocks "senior", "lead", "principal", "staff", "director", "manager", "architect", "head", "chief"
  - **Level indicator rejection:** Blocks " ii", " iii", " iv", " v", " l2", " l3", " l4", "-ii", "-iii", "-iv", " 2,", " 3,"
  - **Spam rejection:** Blocks "data entry", "work from home mobile", "typing job", "back office", "computer operator"
  - **Experience range parsing:** Rejects `2+`, `3+`, `4+`, etc. unless title says "fresher/intern/junior"
  - **Fresher title bonus:** Accepts "fresher", "intern", "trainee", "graduate", "entry level", "junior", "associate", "apprentice", "0-1", "0-2", "sde-1", "sde 1", "software engineer i"

### 8. Resume Textarea Height Increase
- **Problem:** Resume textarea was too small for visibility
- **Fix:** Increased height to 200px

### 9. Popup/Modal Auto-Dismissal
- **Problem:** Login modals, cookie banners, and location popups blocked job extraction
- **Fix:** `_handle_visual_tasks()` closes popups using CSS selectors for close/dismiss buttons, accepts cookie banners, scrolls to load content. Handles LinkedIn sign-in modal, Naukri location popup, and general overlays.

### 10. Experience Filter for "Not Specified" Jobs
- **Problem:** Jobs without experience data were being rejected, reducing yield
- **Fix:** "Not specified" experience is now allowed for freshers (since senior titles are already rejected). This improves yield while maintaining fresher focus.

### 11. Generic Fallback for Shine & LinkedIn
- **Problem:** Strict pattern matching in `_extract_shine_jobs` and `_extract_linkedin_jobs` sometimes returned zero results even when jobs were visible
- **Fix:** Both methods now fall back to `_extract_generic_jobs()` when portal-specific patterns yield no results

### 12. LinkedIn Experience Extraction
- **Problem:** LinkedIn extraction always returned "Not specified" for experience, making the fresher filter ineffective
- **Fix:** Added experience extraction from LinkedIn job cards using patterns: `\d[\s-]*[\d+]*\s*y`, `fresher`, `^0[\s-]*[-–]\s*\d`, `\d+\+\s*years?`

### 13. Job Saver Filter Alignment
- **Problem:** `job_saver.py` had inconsistent fresher filtering compared to orchestrator (allowed up to 2 years min experience)
- **Fix:** Aligned with orchestrator: same senior patterns, spam rejection, fresher title detection. Now strictly requires 0 years unless title explicitly says "fresher/intern/junior"

---

## Current Filtering Logic (Fresher Mode)

A job passes the fresher filter if ALL conditions are met:

1. **Title does NOT contain senior keywords:** senior, lead, principal, staff, director, manager, architect, head, chief
2. **Title does NOT contain level indicators:** ii, iii, iv, v, l2, l3, l4, l5, -2, -3, -4, 2,, 3,
3. **Title does NOT contain spam keywords:** data entry, work from home mobile, typing job, back office, computer operator
4. **Experience range check:**
   - If `X-Y Yrs` and X > 0: REJECT unless title says fresher/intern/junior
   - If `X+ Yrs` and X >= 2: REJECT unless title says fresher/intern/junior
   - If "Not specified" or empty: ALLOW (safe because senior titles already rejected)

---

## Portal Reliability Assessment

| Portal | Reliability | Notes |
|--------|-------------|-------|
| **Naukri** | Medium | Returns 15-20 jobs but all filtered out due to experience requirements |
| **Indeed** | Low | Returns 0 jobs — extraction patterns need improvement |
| **LinkedIn** | High | Returns 25-30 jobs, most pass fresher filter. Best source |
| **Shine** | Low | Returns 3 jobs, often spam (data entry, work from home) |
| **Foundit** | Low | Returns 0 jobs — anti-bot wall blocks extraction |
| **Cutshort** | Unknown | Not tested recently |
| **Glassdoor** | Low | Login modal blocks most content |
| **TimesJobs** | Unknown | Not tested recently |

---

## Known Issues

1. **Naukri returns 0 after filter** — All 15-20 extracted jobs have experience requirements > 0, so they're all rejected for freshers
2. **Indeed returns 0 raw jobs** — Extraction pattern doesn't match Indeed's DOM structure
3. **Foundit returns 0 raw jobs** — Anti-bot detection blocks page rendering
4. **Shine returns spam jobs** — Data entry and work-from-home jobs slip through (partially fixed with spam filter)
5. **LinkedIn experience data inconsistent** — Sometimes extracted, sometimes "Not specified" depending on card rendering
6. **Resume AI analysis fails** — 400/401 errors; relies on regex fallback for skill extraction
7. **Profile fresher detection wrong** — `fresher=False` detected even for fresh graduates

---

## Key Decisions

1. **No cached settings** — All parameters read live from DOM at send time
2. **Experience filter prioritizes title keywords** — "Fresher", "Junior", "Intern" in title overrides missing experience field
3. **Portal loop capped to one pass** — Prevents redundant loads, browser crashes, wasted time
4. **Generic fallback for strict extractors** — Prevents zero-result returns from pattern mismatches
5. **Dual-layer filtering** — Both orchestrator and job_saver filter for redundancy

---

## File Change Summary

| File | Lines Changed | Type |
|------|---------------|------|
| `agents/dual_model_orchestrator.py` | ~40 | Enhanced fresher filter, spam rejection, senior pattern matching |
| `agents/browser_agent/browser_controller.py` | ~20 | Fixed JS/Python syntax error, added LinkedIn experience extraction |
| `agents/job_saver.py` | ~25 | Aligned fresher filter with orchestrator |
| `frontend/public/chat.html` | ~5 | Removed default values, increased resume textarea height |
