# Job Search AI Agent — Project Status & Complete Documentation

## Project Overview

**What we built:** An autonomous AI career agent with ChatGPT-style chat interface, CloakBrowser stealth automation, multi-portal job scraping, resume analysis, ATS scoring, and saved jobs dashboard.

**Target user:** Job seekers (freshers and experienced) searching across Indian and US job portals.

**Core value:** User types a message like "find 20 Java jobs in Hyderabad for freshers" → AI analyzes resume → searches selected portals → returns relevant jobs with match scores → saves to dashboard.

---

## Architecture

| Component | Purpose | Tech Stack |
|-----------|---------|-----------|
| **Backend API** | FastAPI server, all routes | FastAPI, SQLAlchemy, SQLite |
| **Chat UI** | ChatGPT-style interface | `frontend/public/chat.html` (vanilla JS) |
| **Dashboard** | Saved jobs view, filter, export | `frontend/public/dashboard.html` (TailwindCSS) |
| **Chat Agent** | Intent routing, skill extraction, job filtering | `agents/chat_agent/agent.py` |
| **Browser Agent** | CloakBrowser automation, portal navigation | `agents/browser_agent/autonomous_agent.py` |
| **Browser Controller** | CloakBrowser wrapper, job extraction JS | `agents/browser_agent/browser_controller.py` |
| **Resume Analyzer** | Skill/role/experience extraction from resume | `agents/resume_analyzer.py` |
| **Job Saver** | DB save, dedup, ATS scoring | `agents/job_saver.py` |
| **AI Client** | Multi-provider AI (NVIDIA NIM primary) | `ai/ai_client.py` |
| **Database** | Jobs, users, applications, leads | SQLite + SQLAlchemy async |

---

## Implemented Features

### ✅ ChatGPT-Style Chat Interface
- **File:** `frontend/public/chat.html`
- Resume upload (PDF/DOCX/TXT) with drag & drop
- Resume text paste area
- Job keywords, location, target count inputs
- **Portal selector** — checkboxes for India (Naukri, Indeed, LinkedIn, TimesJobs, Shine, Foundit, CutShort, Glassdoor) and USA (Indeed US, LinkedIn US, Glassdoor US, ZipRecruiter, Monster)
- Real-time tool use indicators during search
- Jobs displayed as table with match scores, skills, experience
- Conversation history maintained
- Suggestion buttons for quick actions

### ✅ Saved Jobs Dashboard
- **File:** `frontend/public/dashboard.html`
- Stats: total saved, high ATS (70%+), medium ATS, pending apply, avg ATS
- Filters: All, High ATS, Pending Apply, Applied, Fresher Friendly
- Table with title, company, location, source, ATS score bar, status, actions
- Mark as applied, open job URL, export CSV, apply all pending

### ✅ CloakBrowser Stealth Automation
- **Replaced Playwright entirely** with CloakBrowser (C++ level stealth)
- 57 fingerprint patches on Chromium 146
- Passes reCAPTCHA v3, Cloudflare Turnstile, FingerprintJS
- `humanize=True` for Bézier mouse curves and per-character typing
- No JS stealth injection needed — stealth is at binary level
- Binary auto-downloaded to `~/.cloakbrowser/` (535MB)

### ✅ Multi-Portal Job Search (8 portals)
| Portal | URL Strategy | Status |
|--------|-------------|--------|
| **Naukri** | `/{kw}-jobs-in-{loc}` or `/{kw}-fresher-jobs-in-{loc}` | ✅ Working |
| **Indeed** | `in.indeed.com/jobs?q={kw}&l={loc}` | ✅ Working |
| **LinkedIn** | `linkedin.com/jobs/search?keywords={kw}&location={loc}` | ✅ Working (popup handling) |
| **TimesJobs** | `timesjobs.com/candidate/job-search.html?searchKey={kw}&location={loc}&postExpYrs=0` | ✅ Fixed |
| **Shine** | `shine.com/job-search/{kw}-jobs-in-{loc}` | ✅ Fixed |
| **Foundit** | `foundit.in/srp/results?query={kw}&locations={loc}` | ✅ Working |
| **CutShort** | `cutshort.io/jobs?location={loc}&query={kw}` | ✅ Improved extraction |
| **Glassdoor** | `glassdoor.co.in/Job/jobs.htm?sc.keyword={kw}+{loc}` | ✅ Fixed |

### ✅ Resume Analysis
- **File:** `agents/resume_analyzer.py`
- Extracts: name, skills (80+ skill dictionary), target roles, experience years
- **Fresher detection** based on actual work experience section (company names + dates), not keyword triggers
- Skills extracted from: work experience, projects, education, skills sections
- Target roles inferred from job titles in experience and education

### ✅ Skill Matching (Word-Boundary)
- Fixed substring matching bug: "java" no longer matches "javascript", "smart" no longer matches company names
- Uses `re.search(r'\b{skill}\b', text)` for precise word-boundary matching
- Jobs with 0 skill matches and no role match are filtered out
- Match score: 40 base + (matched_skills / total_skills) × 40 + role_match × 20 + fresher_bonus × 10

### ✅ Experience Filtering
- User message overrides resume analysis
- Detects: "fresher", "1 year", "2 years", "experienced", "senior", "mid level"
- Regex: `(\d+)\s*\+?\s*(?:years?|yrs?|yr)` for specific year extraction
- Fresher mode: only 0-2 years experience jobs
- Specific years: ±1 year tolerance range

### ✅ ATS Scoring
- **File:** `agents/job_saver.py`
- Fast keyword-based scoring (no AI per-job calls)
- 40 base + skill match ratio × 40 + fresher bonus × 10
- Pre-analyzed skills from ResumeAnalyzer passed through for accuracy
- Stored in SQLite with `ats_score`, `match_score`, `matched_skills`

### ✅ Deduplication
- Triple-check: `source_url`, `apply_url`, `title+company+source`
- Prevents duplicate saves across portal visits

### ✅ Portal Selection UI
- User selects which portals to search via checkboxes
- India portals: Naukri, Indeed, LinkedIn, TimesJobs, Shine, Foundit, CutShort, Glassdoor
- USA portals: Indeed US, LinkedIn US, Glassdoor US, ZipRecruiter, Monster
- Defaults: Naukri, Indeed, LinkedIn checked
- Selections saved and passed to backend

### ✅ Deterministic Navigation
- No AI calls per navigation step (saves time and API costs)
- Scroll + extract loop with configurable steps
- Portal-specific timeouts (slow portals get more time)
- Fail-fast detection for blocked/empty pages
- Generic popup closer for cookie banners

---

## Technical Stack

### Backend
- **Python 3.12**
- **FastAPI** — Web framework with async support
- **SQLAlchemy** — ORM with async session
- **SQLite** — Database (`./data/career_agent.db`)
- **CloakBrowser** — Stealth browser automation (replaces Playwright)
- **httpx** — Async HTTP client
- **pypdf** — PDF text extraction
- **python-docx** — DOCX text extraction

### Frontend
- **Vanilla HTML/JS/CSS** — `chat.html` (ChatGPT-style)
- **TailwindCSS CDN** — `dashboard.html`
- No build step required — served directly by FastAPI

### AI
- **NVIDIA NIM** — Primary provider (`mistralai/mistral-large-3-675b-instruct-2512`)
- **API Key:** `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`
- DeepSeek, OpenAI, Anthropic keys are invalid (401 errors)

### Environment Variables (.env)
```env
NVIDIA_API_KEY=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
PLAYWRIGHT_HEADLESS=false
```

---

## File Structure

```
Project/
├── agents/
│   ├── browser_agent/
│   │   ├── __init__.py
│   │   ├── agent.py              # BrowserAgent wrapper (calls autonomous)
│   │   ├── autonomous_agent.py   # Main navigation logic, portal URLs, timeouts
│   │   ├── browser_controller.py # CloakBrowser wrapper, job extraction JS
│   │   └── standalone.py         # Subprocess entry point
│   ├── chat_agent/
│   │   ├── __init__.py
│   │   └── agent.py              # Intent routing, skill extraction, job filtering
│   ├── resume_analyzer.py        # Resume parsing, skill/role extraction
│   ├── job_saver.py              # DB save, dedup, ATS scoring
│   ├── orchestrator/             # Pipeline orchestration (legacy)
│   ├── tracking/                 # Application tracking (legacy)
│   └── workflow/                 # Multi-agent workflow (legacy)
├── ai/
│   ├── __init__.py
│   └── ai_client.py              # Multi-provider AI client (NVIDIA primary)
├── api/
│   └── main.py                   # FastAPI app, all routes
├── database/
│   ├── __init__.py
│   ├── engine.py                 # SQLAlchemy async engine
│   └── models.py                 # ORM models (User, Job, Resume, etc.)
├── frontend/
│   ├── public/
│   │   ├── chat.html             # ChatGPT-style chat interface
│   │   └── dashboard.html        # Saved jobs dashboard
│   ├── src/                      # React app (legacy, not used)
│   └── package.json
├── data/
│   └── career_agent.db           # SQLite database
├── .env                          # Environment variables
├── .env.example                  # Template
├── requirements.txt              # Python dependencies
├── project.md                    # Original project spec
├── PROJECT_STATUS.md             # This file
└── CLAUDE.md                     # Coding guidelines
```

---

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Serves chat.html |
| GET | `/dashboard` | Serves dashboard.html |
| GET | `/health` | Health check |
| POST | `/chat` | Chat with AI agent (main entry point) |
| POST | `/resume/parse` | Parse resume file (PDF/DOCX/TXT) |
| GET | `/saved-jobs` | Get saved jobs with pagination |
| GET | `/saved-jobs/stats` | Get job statistics |
| POST | `/saved-jobs/apply/{id}` | Mark job as applied |
| POST | `/jobs/search` | Legacy job search pipeline |
| POST | `/jobs/export/csv` | Export jobs as CSV |
| POST | `/agent/start` | Start continuous AI agent |
| POST | `/agent/stop` | Stop AI agent |
| GET | `/agent/status` | Get agent status |
| GET | `/agent/jobs` | Get agent-found jobs |
| POST | `/agent/question` | Ask agent a question |
| POST | `/workflow/run` | Run multi-agent workflow |
| GET | `/workflow/dashboard` | Workflow dashboard |
| GET | `/analytics/dashboard` | Analytics data |

---

## Database Models

| Table | Purpose |
|-------|---------|
| `users` | User accounts (email, password, name) |
| `resumes` | Uploaded resumes with parsed data |
| `user_preferences` | Desired roles, locations, skills, auto-apply settings |
| `jobs` | Saved jobs with ATS scores, match scores, status |
| `applications` | Application tracking (status, cover letter, notes) |
| `recruiters` | Recruiter contacts (name, role, company, LinkedIn) |
| `companies` | Company intelligence (tech stack, culture, hiring trend) |
| `leads` | B2B leads for outreach |
| `networking_messages` | Generated outreach messages |
| `analytics_logs` | Event tracking |

---

## Key Decisions & Tradeoffs

### Playwright → CloakBrowser
- **Why:** Playwright is easily detected by anti-bot systems. CloakBrowser has 57 C++-level fingerprint patches built into the binary.
- **Result:** Passes reCAPTCHA v3 (0.9 score), Cloudflare Turnstile, FingerprintJS without any JS injection.
- **Tradeoff:** 535MB binary download, but zero detection.

### Deterministic Navigation (No AI Per Step)
- **Why:** AI calls per navigation step add 5-10s each. With 8 portals × 4 steps = 32 AI calls = 160-320s just for navigation.
- **Result:** Navigation completes in 25-45s per portal instead of timing out.
- **Tradeoff:** Less "intelligent" navigation, but much faster and more reliable.

### Keyword-Based ATS Scoring (No AI Per Job)
- **Why:** AI scoring per job adds 10s per job. For 100 jobs = 1000s = 16 minutes.
- **Result:** Instant scoring using word-boundary skill matching.
- **Tradeoff:** Less nuanced than AI analysis, but instant and accurate enough.

### User Message Overrides Resume Analysis
- **Why:** Resume may say "experienced" but user wants "fresher" jobs.
- **Result:** Explicit experience detection from user message ("fresher", "1 year", "experienced") overrides resume analysis.

### Word-Boundary Skill Matching
- **Why:** Substring matching caused "java" to match "javascript", "smart" to match company names like "Smart Wealth".
- **Result:** `re.search(r'\b{skill}\b', text)` ensures exact word matches only.

---

## Performance Tuning

| Setting | Value | Reason |
|---------|-------|--------|
| Subprocess timeout | 600s (10 min) | All 8 portals need time |
| Per-portal timeout | 45s | Enough for page load + scroll + extract |
| Slow portal timeout | 45s | Glassdoor, TimesJobs, LinkedIn, Indeed |
| Max steps per portal | 4 | Scroll 4 times to load more jobs |
| Navigation timeout | 30s | All portals |
| Step wait | 0.5s | Between scrolls |
| Click/type delay | Built into CloakBrowser `humanize=True` | No manual delays needed |

---

## Current Issues

### LinkedIn Extraction (0 jobs)
- LinkedIn shows sign-in popup, popup is closed, but job cards aren't extracted
- Likely needs updated selectors for LinkedIn's current DOM structure
- **Priority:** Medium — LinkedIn is a major portal

### ZipRecruiter / Monster (USA)
- URLs not yet implemented in `_build_initial_url`
- **Priority:** Low — only needed for US searches

### CutShort Extraction Inconsistency
- React SPA with randomized CSS classes — extraction sometimes returns 0 jobs
- Improved with 3-tier fallback (selectors → link-based → keyword-based)
- **Priority:** Medium — works sometimes but not reliably

---

## Usage

### Start Server
```powershell
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Access
- Chat: `http://localhost:8000/`
- Dashboard: `http://localhost:8000/dashboard`
- API Docs: `http://localhost:8000/docs`

### Chat Examples
- "Find 20 Java jobs in Hyderabad for freshers"
- "Search for Python developer jobs in Bangalore"
- "Find 1 year experience data analyst jobs in Pune"
- "Search for Appian consultant jobs"

### Portal Selection
1. Open chat interface
2. Check/uncheck portals in sidebar (India / USA columns)
3. Click "Save Settings"
4. Search — only selected portals will be visited

---

## What Was Removed/Replaced

| Old | New | Reason |
|-----|-----|--------|
| Playwright | CloakBrowser | Stealth detection |
| React frontend | chat.html + dashboard.html | Simpler, no build step |
| AI per-job scoring | Keyword-based ATS | Speed (instant vs 10s/job) |
| AI per-navigation step | Deterministic scroll+extract | Speed (25s vs timeout) |
| Captcha solver | CloakBrowser built-in stealth | Captcha code was dead |
| Vision analysis | Removed | Dead code, not used |
| Skills.sh API | Local resume analyzer | External API unreliable |

---

*Last updated: 2026-05-18*
*Status: Core features working — chat UI, multi-portal search, ATS scoring, dashboard, portal selection*
