# Combo AI Agent

A production-grade combo application that unifies an **Autonomous AI Career Agent** (job search, resume matching, auto-apply) with a **B2B Lead Generation AI Agent** (company intelligence, pain scoring, outreach generation).

## What It Does

- **Job Discovery**: Searches Indeed, LinkedIn, Naukri for jobs
- **AI Job Intelligence**: Analyzes descriptions, extracts skills, detects fresher roles
- **Resume Match Engine**: Generates ATS scores and compatibility rankings
- **Auto-Apply Agent**: Browser automation via Playwright
- **Recruiter Finder**: Discovers hiring managers from public data
- **Networking Agent**: Generates personalized outreach messages
- **Lead Generation**: Analyzes companies for automation pain signals
- **Outreach Engine**: AI-generated B2B cold messages
- **Analytics Dashboard**: Tracks applications, outreach, and pipeline metrics

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, SQLAlchemy, asyncpg |
| Frontend | React, TailwindCSS, Recharts, Vite |
| AI | OpenAI / DeepSeek / Anthropic (multi-provider) |
| Browser | Playwright |
| Scraping | BeautifulSoup, httpx, fake-useragent |
| Database | PostgreSQL + Redis |
| Queue | Celery (optional) |
| Deploy | Docker + Docker Compose |

## Quick Start

### 1. Clone & Setup

```bash
cd "Harshith Games/Project"
cp .env.example .env
# Edit .env and add your AI API keys
```

### 2. Run with Docker

```bash
docker-compose up --build
```

- API: http://localhost:8000
- Frontend: http://localhost:3000 (via Vite proxy)

### 3. Run Backend Only (local Python)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start DB & Redis (if using Docker for services)
docker-compose up -d db redis

# Run API
uvicorn api.main:app --reload --port 8000
```

### 4. Run Frontend Only

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Health check |
| POST | `/jobs/search` | Run job discovery + match pipeline |
| POST | `/leads/enrich` | Enrich company leads with AI |
| POST | `/combo/run` | Run both pipelines in parallel |
| GET | `/analytics/dashboard` | Get pipeline analytics |
| GET | `/analytics/applications` | List tracked applications |
| GET | `/analytics/outreach` | List tracked outreach |
| POST | `/resume/parse` | Upload and parse a resume file |

## Agent Architecture

| Agent | File | Purpose |
|-------|------|---------|
| Orchestrator | `agents/orchestrator/orchestrator.py` | Coordinates all agents |
| Job Discovery | `agents/job_discovery/discovery.py` | Scrapes job boards |
| Job Intelligence | `agents/job_intelligence/intelligence.py` | AI analysis of JDs |
| Resume Match | `agents/resume_match/matcher.py` | ATS scoring |
| Company Intel | `agents/company_intelligence/intel.py` | B2B lead enrichment |
| People Finder | `agents/people_finder/finder.py` | Recruiter discovery |
| Networking | `agents/networking/messages.py` | Outreach generation |
| Auto Apply | `agents/auto_apply/browser_agent.py` | Playwright automation |
| Tracking | `agents/tracking/tracker.py` | Application tracking |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `PRIMARY_AI_PROVIDER` | Yes | `deepseek`, `openai`, or `anthropic` |
| `DEEPSEEK_API_KEY` | If provider=deepseek | DeepSeek API key |
| `OPENAI_API_KEY` | If provider=openai | OpenAI API key |
| `ANTHROPIC_API_KEY` | If provider=anthropic | Anthropic API key |
| `SMTP_HOST` | No | For email outreach |
| `SMTP_USER` | No | SMTP username |
| `SMTP_PASSWORD` | No | SMTP password |

## Folder Structure

```
career_agent/
├── agents/               # 9 modular AI agents
├── ai/                   # Multi-provider AI client + prompts
├── api/                  # FastAPI routes
├── browser/              # Playwright helpers
├── config/               # Settings, env
├── database/             # SQLAlchemy models + engine
├── docker/               # Docker assets
├── frontend/             # React + Tailwind dashboard
├── scrapers/             # Job board scrapers
├── workers/              # Celery tasks
├── tests/                # Pytest suite
├── data/                 # Local data storage
├── logs/                 # Application logs
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Compliance & Safety

- Only scrapes publicly visible data
- Respects rate limits
- No private data harvesting
- No bypassing of platform security
- AI-generated outreach is reviewed before sending

## License

MIT
