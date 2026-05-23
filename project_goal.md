# Project Goal: Complete AI-Powered Job Application Agent

## Vision Statement

Transform the job search experience from manual, time-consuming work into a fully automated, AI-driven process where users simply upload their resume and the system handles everything - from finding relevant jobs to applying and networking with hiring managers.

---

## Current State vs. Target State

### ✅ Current System (What We Have)
- Multi-portal job scraping (8 portals: Naukri, Indeed, LinkedIn, TimesJobs, Shine, Foundit, CutShort, Glassdoor)
- Resume analysis (skills, experience extraction)
- Basic ATS scoring
- Job filtering by keywords/location/experience
- Saved jobs dashboard
- Manual application process

### 🎯 Target System (What We Want)

**A complete end-to-end AI agent that:**
1. Scrapes jobs from multiple portals intelligently
2. Deeply matches jobs to user's resume and profile
3. Generates custom resumes for each job
4. Finds hiring managers and recruiters
5. Sends personalized outreach messages
6. Auto-applies to jobs with one click
7. Tracks everything in an intelligent dashboard

---

## Core Problems We're Solving

### Problem 1: Current Scraping is Brittle
- **Issue:** Hardcoded CSS selectors break when portals update
- **Impact:** Requires monthly maintenance, portals fail silently
- **Solution:** Vision-guided scraping with Mistral Pixtral (adaptive, self-healing)

### Problem 2: Poor Job Matching
- **Issue:** Basic keyword matching misses semantic relevance
- **Impact:** Users see irrelevant jobs, waste time filtering
- **Solution:** Deep AI semantic matching with skill gap analysis

### Problem 3: Generic Applications
- **Issue:** One resume for all jobs = low ATS scores
- **Impact:** Applications get rejected by ATS systems
- **Solution:** Custom resume generation per job with ATS optimization

### Problem 4: No Networking Support
- **Issue:** Users don't know who to contact at companies
- **Impact:** Miss opportunities for referrals and direct outreach
- **Solution:** Automated recruiter intelligence and contact finding

### Problem 5: Manual Application Process
- **Issue:** Users must manually fill forms, upload resumes, answer questions
- **Impact:** Time-consuming, error-prone, discouraging
- **Solution:** Vision-guided auto-apply agent

---

## Feature Roadmap

### Phase 1: Enhanced Job Matching & Personalization (Priority: HIGH)
**Timeline:** 2-3 weeks

#### Features:
1. **Deep Resume-Job Matching**
   - Semantic similarity analysis (not just keyword matching)
   - Calculate fit score (0-100%) for each job
   - Consider: skills, experience, education, projects, achievements
   - Rank jobs by match quality

2. **Skill Gap Analysis**
   - Identify missing skills for each job
   - Highlight required vs. optional skills
   - Show which skills user has vs. needs
   - Suggest learning resources for gaps

3. **Custom Resume Generator**
   - Generate tailored resume for EACH job
   - Optimize for ATS keywords from job description
   - Highlight relevant experience and projects
   - Reorder sections based on job requirements
   - Format according to company preferences
   - Export as PDF/DOCX

4. **"Why You Should Get This Job" Pitch**
   - AI-generated personalized pitch
   - Highlight unique qualifications
   - Address potential concerns (gaps, transitions)
   - Provide talking points for interviews

**Tech Stack:**
- AI: Mistral Large 3 (free experiment plan)
- Embeddings: Sentence transformers for semantic matching
- Resume generation: Python-DOCX, ReportLab

**Success Metrics:**
- Match accuracy: 85%+ user satisfaction
- Custom resume generation: <10 seconds per job
- ATS score improvement: +20% average

---

### Phase 2: Vision-Guided Adaptive Scraping (Priority: HIGH)
**Timeline:** 2-3 weeks

#### Features:
1. **Vision-Guided Navigation**
   - Replace hardcoded selectors with vision analysis
   - Mistral Pixtral analyzes screenshots
   - Decides actions: click, scroll, type, extract
   - Executes via PyAutoGUI + CloakBrowser

2. **Self-Healing Scraping**
   - Adapts automatically when portals update
   - No manual selector updates needed
   - Handles popups, cookie banners, sign-in prompts
   - Recovers from errors intelligently

3. **Universal Portal Support**
   - Same code works on ALL portals
   - Easy to add new portals (just provide URL)
   - No portal-specific logic required

4. **Hybrid Extraction**
   - Vision for navigation (adaptive)
   - JavaScript for extraction (fast, structured)
   - Best of both worlds

**Tech Stack:**
- Vision Model: Mistral Pixtral 12B (free experiment plan, 2 RPM)
- Fallback: Google Gemini 2.5 Flash (free, 15 RPM)
- Browser: CloakBrowser (stealth)
- Execution: PyAutoGUI

**Success Metrics:**
- Portal reliability: 90%+ success rate
- Maintenance: Zero selector updates per month
- Speed: 2-3 minutes per portal (acceptable)

---

### Phase 3: Recruiter Intelligence & Contact Finding (Priority: MEDIUM)
**Timeline:** 3-4 weeks

#### Features:
1. **LinkedIn Hiring Manager Finder**
   - Scrape LinkedIn for company employees
   - Identify: HRs, recruiters, hiring managers, team leads
   - Filter by role, seniority, department
   - Extract: name, title, LinkedIn URL, profile summary

2. **Contact Information Extraction**
   - Find email addresses (company website, LinkedIn, Hunter.io)
   - Find phone numbers (if publicly available)
   - Verify email deliverability
   - Store in database with job association

3. **Company Intelligence**
   - Scrape company website for tech stack
   - Extract company culture, values, mission
   - Find recent news, funding, growth signals
   - Identify pain points and hiring needs

4. **Relationship Mapping**
   - Find mutual connections on LinkedIn
   - Identify alumni from same school/company
   - Suggest warm introduction paths

**Tech Stack:**
- LinkedIn scraping: Vision-guided (Mistral Pixtral)
- Email finding: Hunter.io API, Clearbit, manual extraction
- Company intelligence: Web scraping + AI analysis
- Storage: SQLite with recruiter/company tables

**Success Metrics:**
- Contact find rate: 60%+ jobs have hiring manager info
- Email accuracy: 80%+ valid emails
- Company intel: 90%+ jobs have company data

---

### Phase 4: Automated Outreach (Priority: MEDIUM)
**Timeline:** 2-3 weeks

#### Features:
1. **Cold Email Generation**
   - Personalized emails to hiring managers
   - Reference: job posting, company news, mutual connections
   - Tone: professional, concise, value-focused
   - Include: resume attachment, portfolio link
   - A/B test different templates

2. **LinkedIn Message Generation**
   - Connection request messages (300 char limit)
   - Follow-up messages after connection
   - Reference: job posting, profile, mutual interests
   - Tone: friendly, professional, genuine

3. **Email Sending Automation**
   - Send emails via SMTP (user's email account)
   - Track: sent, opened, replied
   - Schedule: optimal send times
   - Follow-up: automated reminders if no response

4. **LinkedIn Automation** (Optional - requires caution)
   - Send connection requests (rate-limited)
   - Send messages after connection
   - Track: sent, accepted, replied
   - **Warning:** LinkedIn may ban accounts for automation

**Tech Stack:**
- Email generation: Mistral Large 3
- Email sending: SMTP (Gmail, Outlook)
- Email tracking: Mailgun, SendGrid (optional)
- LinkedIn automation: Selenium + CloakBrowser (risky)

**Success Metrics:**
- Email generation quality: 85%+ user approval
- Email delivery rate: 95%+
- Response rate: 10-15% (industry standard)

**Legal/Ethical Considerations:**
- ⚠️ LinkedIn automation violates ToS (risk of ban)
- ✅ Email outreach is legal (CAN-SPAM compliant)
- ✅ User must approve messages before sending
- ✅ Provide opt-out mechanism

---

### Phase 5: Auto-Apply Agent (Priority: HIGH)
**Timeline:** 4-5 weeks

#### Features:
1. **Vision-Guided Form Filling**
   - Analyze application form with vision model
   - Identify: text fields, dropdowns, checkboxes, file uploads
   - Fill fields automatically from resume data
   - Handle multi-page applications

2. **Screening Question Answering**
   - AI answers based on resume and job description
   - Handle: yes/no, multiple choice, text responses
   - Provide consistent, honest answers
   - Flag questions that need user review

3. **Resume Upload Automation**
   - Upload custom-generated resume for each job
   - Handle different file formats (PDF, DOCX)
   - Verify upload success

4. **Application Submission**
   - Review filled form before submission
   - Submit application
   - Capture confirmation number/email
   - Track application status

5. **One-Click Apply**
   - User clicks "Apply" in dashboard
   - Agent handles entire process
   - User receives notification on completion
   - Option to review before submission

**Tech Stack:**
- Vision Model: Mistral Pixtral (form analysis)
- Browser: CloakBrowser (stealth)
- Execution: PyAutoGUI
- AI: Mistral Large 3 (question answering)

**Success Metrics:**
- Application success rate: 85%+
- Time per application: 2-5 minutes
- User intervention rate: <10%

**Safety Features:**
- Preview before submission
- User approval for sensitive questions
- Rollback on errors
- Application audit log

---

## Enhanced Dashboard Features

### Job Card Enhancements
- **Match Score Badge:** 0-100% with color coding (red/yellow/green)
- **Skill Gap Indicator:** "Missing 3 skills" with expandable list
- **Custom Resume Preview:** Thumbnail of tailored resume
- **Hiring Manager Card:** Photo, name, title, LinkedIn link
- **Outreach Status:** "Email sent", "Connection pending", "Replied"
- **Apply Button:** One-click auto-apply

### New Dashboard Sections
1. **Match Quality Filter**
   - Excellent (90-100%)
   - Good (70-89%)
   - Fair (50-69%)
   - Poor (<50%)

2. **Application Pipeline**
   - To Apply (pending)
   - Applied (submitted)
   - In Review (recruiter viewed)
   - Interview (scheduled)
   - Rejected
   - Offer

3. **Outreach Tracker**
   - Emails sent: 15
   - Connections pending: 8
   - Responses received: 3
   - Meetings scheduled: 1

4. **Analytics Dashboard**
   - Applications per day
   - Response rate over time
   - Top matching skills
   - Most responsive companies

---

## Technical Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Enhanced)                       │
│  - Chat interface (existing)                                 │
│  - Enhanced dashboard with match scores                      │
│  - Custom resume preview                                     │
│  - Hiring manager cards                                      │
│  - Outreach tracker                                          │
│  - One-click apply button                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                     │
│  - Existing routes (chat, resume parse, saved jobs)         │
│  - New: /jobs/match (deep matching)                         │
│  - New: /jobs/{id}/custom-resume (generate)                 │
│  - New: /jobs/{id}/recruiters (find contacts)               │
│  - New: /jobs/{id}/outreach (send messages)                 │
│  - New: /jobs/{id}/apply (auto-apply)                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    AI ORCHESTRATOR                           │
│  - Route requests to appropriate agents                      │
│  - Manage multi-step workflows                               │
│  - Handle errors and retries                                 │
│  - Track progress and status                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    SPECIALIZED AGENTS                        │
│                                                              │
│  1. Vision-Guided Scraper Agent                             │
│     - Mistral Pixtral for navigation                        │
│     - CloakBrowser for stealth                              │
│     - PyAutoGUI for execution                               │
│                                                              │
│  2. Job Matching Agent                                      │
│     - Semantic similarity analysis                          │
│     - Skill gap identification                              │
│     - Ranking and scoring                                   │
│                                                              │
│  3. Resume Generator Agent                                  │
│     - Custom resume per job                                 │
│     - ATS optimization                                      │
│     - PDF/DOCX export                                       │
│                                                              │
│  4. Recruiter Intelligence Agent                            │
│     - LinkedIn scraping                                     │
│     - Contact extraction                                    │
│     - Company research                                      │
│                                                              │
│  5. Outreach Agent                                          │
│     - Email generation                                      │
│     - LinkedIn message generation                           │
│     - Sending automation                                    │
│                                                              │
│  6. Auto-Apply Agent                                        │
│     - Form analysis                                         │
│     - Field filling                                         │
│     - Application submission                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER (SQLite)                       │
│  - users, resumes, jobs (existing)                          │
│  - New: job_matches (scores, gaps)                          │
│  - New: custom_resumes (per job)                            │
│  - New: recruiters (contacts)                               │
│  - New: companies (intelligence)                            │
│  - New: outreach_messages (tracking)                        │
│  - New: applications (status tracking)                      │
└─────────────────────────────────────────────────────────────┘
```

---

## AI Model Strategy

### Primary: Mistral AI (Free Experiment Plan)
- **Model:** Mistral Large 3 (text) + Pixtral 12B (vision)
- **Cost:** FREE (1B tokens/month)
- **Rate Limit:** 2 RPM (manageable with pacing)
- **Use Cases:**
  - Vision-guided navigation
  - Job matching analysis
  - Resume generation
  - Email/message generation
  - Question answering

### Fallback: Google Gemini (Free Tier)
- **Model:** Gemini 2.5 Flash
- **Cost:** FREE (1,500 requests/day)
- **Rate Limit:** 15 RPM
- **Use Cases:**
  - Burst traffic handling
  - Backup when Mistral rate-limited
  - Faster inference for urgent tasks

### Multi-Provider Rotation
- Rotate between Mistral and Gemini
- Maximize free tier capacity
- Total: ~4,000 requests/day combined

---

## Database Schema Updates

### New Tables

```sql
-- Job match scores and analysis
CREATE TABLE job_matches (
    id INTEGER PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    user_id INTEGER REFERENCES users(id),
    match_score REAL,  -- 0-100
    skill_match_score REAL,
    experience_match_score REAL,
    education_match_score REAL,
    matched_skills TEXT,  -- JSON array
    missing_skills TEXT,  -- JSON array
    why_good_fit TEXT,  -- AI-generated pitch
    created_at TIMESTAMP
);

-- Custom resumes per job
CREATE TABLE custom_resumes (
    id INTEGER PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    user_id INTEGER REFERENCES users(id),
    resume_text TEXT,
    resume_pdf_path TEXT,
    resume_docx_path TEXT,
    ats_optimized BOOLEAN,
    created_at TIMESTAMP
);

-- Hiring managers and recruiters
CREATE TABLE recruiters (
    id INTEGER PRIMARY KEY,
    company_name TEXT,
    name TEXT,
    title TEXT,
    linkedin_url TEXT,
    email TEXT,
    phone TEXT,
    department TEXT,
    seniority TEXT,
    profile_summary TEXT,
    created_at TIMESTAMP
);

-- Company intelligence
CREATE TABLE companies (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    website TEXT,
    tech_stack TEXT,  -- JSON array
    culture TEXT,
    recent_news TEXT,  -- JSON array
    funding_stage TEXT,
    employee_count INTEGER,
    hiring_signals TEXT,  -- JSON array
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Outreach messages
CREATE TABLE outreach_messages (
    id INTEGER PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    recruiter_id INTEGER REFERENCES recruiters(id),
    message_type TEXT,  -- 'email' or 'linkedin'
    subject TEXT,
    body TEXT,
    status TEXT,  -- 'draft', 'sent', 'opened', 'replied'
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    replied_at TIMESTAMP
);

-- Application tracking
CREATE TABLE applications (
    id INTEGER PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    user_id INTEGER REFERENCES users(id),
    custom_resume_id INTEGER REFERENCES custom_resumes(id),
    status TEXT,  -- 'pending', 'submitted', 'in_review', 'interview', 'rejected', 'offer'
    confirmation_number TEXT,
    applied_at TIMESTAMP,
    updated_at TIMESTAMP,
    notes TEXT
);
```

---

## Success Metrics

### Phase 1: Enhanced Matching
- Match accuracy: 85%+ user satisfaction
- Custom resume generation: <10s per job
- ATS score improvement: +20% average

### Phase 2: Vision Scraping
- Portal reliability: 90%+ success rate
- Maintenance: 0 selector updates/month
- Speed: 2-3 min per portal

### Phase 3: Recruiter Intelligence
- Contact find rate: 60%+ jobs
- Email accuracy: 80%+ valid
- Company intel: 90%+ jobs

### Phase 4: Outreach
- Email quality: 85%+ user approval
- Delivery rate: 95%+
- Response rate: 10-15%

### Phase 5: Auto-Apply
- Success rate: 85%+
- Time per application: 2-5 min
- User intervention: <10%

### Overall Platform
- User satisfaction: 90%+
- Time saved: 20+ hours/week per user
- Interview rate: 2x improvement
- Job offer rate: 1.5x improvement

---

## Risks & Mitigation

### Technical Risks
1. **Vision model accuracy**
   - Risk: Misidentifies elements, clicks wrong buttons
   - Mitigation: Validation checks, retry logic, user review

2. **Rate limits**
   - Risk: Free tier limits hit during peak usage
   - Mitigation: Multi-provider rotation, request pacing, upgrade path

3. **Portal blocking**
   - Risk: Job portals detect and block automation
   - Mitigation: CloakBrowser stealth, human-like behavior, rate limiting

### Legal/Ethical Risks
1. **LinkedIn automation**
   - Risk: Account bans for violating ToS
   - Mitigation: User consent, rate limiting, optional feature

2. **Email spam**
   - Risk: Emails marked as spam, sender reputation damage
   - Mitigation: CAN-SPAM compliance, user approval, opt-out links

3. **Data privacy**
   - Risk: Storing sensitive user data (resumes, contacts)
   - Mitigation: Encryption, GDPR compliance, user data controls

### Business Risks
1. **Scalability**
   - Risk: Free tier insufficient for growth
   - Mitigation: Paid tier upgrade path, usage-based pricing

2. **Competition**
   - Risk: Similar products in market
   - Mitigation: Focus on quality, user experience, unique features

---

## Monetization Strategy (Future)

### Free Tier
- 10 job searches per month
- Basic matching and ATS scoring
- Manual application process

### Pro Tier ($29/month)
- Unlimited job searches
- Custom resume generation
- Recruiter intelligence
- Email outreach (50/month)

### Premium Tier ($99/month)
- Everything in Pro
- Auto-apply agent
- LinkedIn automation
- Priority support
- Advanced analytics

### Enterprise Tier (Custom)
- White-label solution
- API access
- Custom integrations
- Dedicated support

---

## Timeline Summary

| Phase | Duration | Priority | Dependencies |
|-------|----------|----------|--------------|
| Phase 1: Enhanced Matching | 2-3 weeks | HIGH | None |
| Phase 2: Vision Scraping | 2-3 weeks | HIGH | None |
| Phase 3: Recruiter Intelligence | 3-4 weeks | MEDIUM | Phase 2 |
| Phase 4: Outreach Automation | 2-3 weeks | MEDIUM | Phase 3 |
| Phase 5: Auto-Apply | 4-5 weeks | HIGH | Phase 2 |

**Total Timeline:** 13-18 weeks (3-4.5 months) for complete system

---

## Next Steps

1. **Review and approve this roadmap**
2. **Prioritize phases** (recommend: Phase 1 + Phase 2 first)
3. **Create detailed spec** for Phase 1
4. **Set up Mistral Experiment Plan** (free API access)
5. **Begin implementation**

---

## Notes

- This is an ambitious, comprehensive project
- Each phase delivers standalone value
- Can be built incrementally
- Free tier AI models make this economically viable
- Vision-guided automation is the key enabler
- Focus on user experience and reliability
- Legal/ethical compliance is critical

---

*Last updated: 2026-05-18*
*Status: Planning phase - awaiting approval to begin implementation*
