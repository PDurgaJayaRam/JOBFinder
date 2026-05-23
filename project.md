# Autonomous AI Career Agent
## Production-Grade AI Job Search Platform with ChatGPT-Style Interface

---

# Project Overview

Build a production-grade AI-powered Autonomous Career Agent that acts as a personal job search copilot. User types natural language requests like "find 20 Java jobs in Hyderabad for freshers" and the AI handles everything: resume analysis, multi-portal search, skill matching, ATS scoring, and job saving.

**Target user:** Job seekers (freshers and experienced) in India and USA.

**Core value:** One chat interface replaces manual searching across 8+ job portals with intelligent filtering and scoring.

---

# Current Architecture (As Built)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI (Python 3.12), SQLAlchemy async, SQLite |
| **Frontend** | Vanilla HTML/JS (chat.html + dashboard.html), TailwindCSS CDN |
| **Browser Automation** | CloakBrowser (C++ stealth, 57 fingerprint patches) |
| **AI Provider** | NVIDIA NIM (mistral-large-3-675b-instruct-2512) |
| **Database** | SQLite (`./data/career_agent.db`) |

## File Structure

```
Project/
├── agents/
│   ├── browser_agent/          # CloakBrowser automation
│   │   ├── agent.py            # BrowserAgent wrapper
│   │   ├── autonomous_agent.py # Portal navigation, URL building, timeouts
│   │   ├── browser_controller.py # CloakBrowser wrapper, job extraction JS
│   │   └── standalone.py       # Subprocess entry point
│   ├── chat_agent/
│   │   └── agent.py            # Intent routing, skill extraction, job filtering
│   ├── resume_analyzer.py      # Resume parsing, skill/role extraction
│   └── job_saver.py            # DB save, dedup, ATS scoring
├── ai/
│   └── ai_client.py            # Multi-provider AI client
├── api/
│   └── main.py                 # FastAPI app, all routes
├── database/
│   ├── engine.py               # SQLAlchemy async engine
│   └── models.py               # ORM models
├── frontend/
│   └── public/
│       ├── chat.html           # ChatGPT-style chat interface
│       └── dashboard.html      # Saved jobs dashboard
└── data/
    └── career_agent.db         # SQLite database
```

---

# Core Features Implemented

## 1. ChatGPT-Style Chat Interface
- **File:** `frontend/public/chat.html`
- Resume upload (PDF/DOCX/TXT) with drag & drop or paste
- Job keywords, location, target count inputs
- **Portal selector** — checkboxes for India and USA portals
- Real-time tool use indicators during search
- Jobs displayed as table with match scores, skills, experience
- Conversation history maintained across messages

## 2. Saved Jobs Dashboard
- **File:** `frontend/public/dashboard.html`
- Stats: total saved, high ATS (70%+), medium ATS, pending, avg ATS
- Filters: All, High ATS, Pending Apply, Applied, Fresher Friendly
- Table with title, company, location, source, ATS score bar, status
- Actions: mark applied, open URL, export CSV, apply all pending

## 3. CloakBrowser Stealth Automation
- Replaced Playwright with CloakBrowser (C++ level stealth)
- 57 fingerprint patches on Chromium 146
- Passes reCAPTCHA v3, Cloudflare Turnstile, FingerprintJS
- `humanize=True` for human-like mouse/keyboard behavior
- No JS stealth injection needed

## 4. Multi-Portal Job Search
| Portal | Region | Status |
|--------|--------|--------|
| Naukri | India | ✅ Working |
| Indeed | India | ✅ Working |
| LinkedIn | India | ✅ Working (popup handling) |
| TimesJobs | India | ✅ Fixed URL |
| Shine | India | ✅ Fixed URL |
| Foundit | India | ✅ Working |
| CutShort | India | ✅ Improved extraction |
| Glassdoor | India | ✅ Fixed URL |
| Indeed US | USA | ✅ Working |
| LinkedIn US | USA | ✅ Working |
| Glassdoor US | USA | ✅ Working |
| ZipRecruiter | USA | ⏳ URL needed |
| Monster | USA | ⏳ URL needed |

## 5. Resume Analysis
- Extracts: name, skills (80+ skill dictionary), target roles, experience years
- Fresher detection based on actual work experience (company names + dates)
- Skills extracted from work experience, projects, education, skills sections
- Target roles inferred from job titles in experience and education

## 6. Skill Matching (Word-Boundary)
- Uses `re.search(r'\b{skill}\b', text)` for precise matching
- "java" does NOT match "javascript", "smart" does NOT match company names
- Jobs with 0 skill matches and no role match are filtered out
- Match score: 40 base + skill ratio × 40 + role match × 20 + fresher bonus × 10

## 7. Experience Filtering
- User message overrides resume analysis
- Detects: "fresher", "1 year", "2 years", "experienced", "senior"
- Regex: `(\d+)\s*\+?\s*(?:years?|yrs?|yr)` for specific years
- Fresher mode: only 0-2 years experience jobs
- Specific years: ±1 year tolerance

## 8. ATS Scoring
- Fast keyword-based scoring (no AI per-job calls)
- Pre-analyzed skills from ResumeAnalyzer for accuracy
- Stored in SQLite with `ats_score`, `match_score`, `matched_skills`

## 9. Deduplication
- Triple-check: `source_url`, `apply_url`, `title+company+source`
- Prevents duplicate saves across portal visits

## 10. Portal Selection UI
- User selects which portals to search via checkboxes
- India portals: Naukri, Indeed, LinkedIn, TimesJobs, Shine, Foundit, CutShort, Glassdoor
- USA portals: Indeed US, LinkedIn US, Glassdoor US, ZipRecruiter, Monster
- Defaults: Naukri, Indeed, LinkedIn checked

---

# API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Serves chat.html |
| GET | `/dashboard` | Serves dashboard.html |
| POST | `/chat` | Chat with AI agent (main entry) |
| POST | `/resume/parse` | Parse resume file |
| GET | `/saved-jobs` | Get saved jobs |
| GET | `/saved-jobs/stats` | Get job statistics |
| POST | `/saved-jobs/apply/{id}` | Mark job as applied |

---

# Database Models

| Table | Key Fields |
|-------|-----------|
| `users` | email, hashed_password, full_name |
| `resumes` | user_id, filename, text_content, skills, experience_years |
| `user_preferences` | user_id, desired_roles, desired_locations, skills |
| `jobs` | title, company, location, source, ats_score, match_score, status |
| `applications` | user_id, job_id, status, cover_letter, applied_at |
| `recruiters` | name, role, company, linkedin_url, email |
| `companies` | name, website, tech_stack, culture, hiring_trend |
| `leads` | company_name, email, pain_signals, priority |

---

# Key Decisions

### Playwright → CloakBrowser
Playwright is easily detected. CloakBrowser has 57 C++-level fingerprint patches built into the binary. Passes all anti-bot systems without JS injection.

### Deterministic Navigation
No AI calls per navigation step. Scroll + extract loop completes in 25-45s per portal instead of timing out.

### Keyword-Based ATS Scoring
Instant scoring using word-boundary skill matching. No AI per-job calls (saves 10s per job).

### User Message Overrides Resume
Explicit experience detection from user message overrides resume analysis. "fresher" in message = fresher mode regardless of resume.

---

# Performance Settings

| Setting | Value |
|---------|-------|
| Subprocess timeout | 600s (10 min) |
| Per-portal timeout | 45s |
| Max steps per portal | 4 |
| Navigation timeout | 30s |
| Step wait | 0.5s |

---

# Usage

```powershell
# Start server
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# Access
# Chat: http://localhost:8000/
# Dashboard: http://localhost:8000/dashboard
```

### Chat Examples
- "Find 20 Java jobs in Hyderabad for freshers"
- "Search for Python developer jobs in Bangalore"
- "Find 1 year experience data analyst jobs in Pune"

---

# Current Issues

1. **LinkedIn extraction** — Popup closed but 0 jobs extracted (needs selector update)
2. **CutShort inconsistency** — React SPA, sometimes 0 jobs (3-tier fallback helps)
3. **ZipRecruiter/Monster URLs** — Not yet implemented for USA searches

---

# What Was Removed

| Old | New | Reason |
|-----|-----|--------|
| Playwright | CloakBrowser | Stealth detection |
| React frontend | chat.html + dashboard.html | Simpler, no build |
| AI per-job scoring | Keyword-based ATS | Speed |
| AI per-navigation step | Deterministic scroll+extract | Speed |
| Captcha solver | CloakBrowser stealth | Dead code |
| Vision analysis | Removed | Dead code |
| Skills.sh API | Local resume analyzer | Unreliable |

---

*Last updated: 2026-05-18*
