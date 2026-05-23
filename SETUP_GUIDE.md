# Setup Guide: Enhanced Job Matching Features

## Overview

This guide will help you set up the new AI-powered job matching features without breaking your existing system.

**New Features:**
- ✅ Deep semantic job matching with AI
- ✅ Skill gap analysis
- ✅ Custom resume generation per job
- ✅ "Why you're a good fit" AI explanations
- ✅ Enhanced dashboard with match scores

**Your existing system remains fully functional!**

---

## Step 1: Get Free API Keys

### Mistral AI (Primary - FREE)

1. Go to: https://console.mistral.ai/
2. Sign up with email
3. Go to: https://console.mistral.ai/upgrade/plans
4. Click "Experiment for free"
5. Verify phone number
6. Go to: https://console.mistral.ai/api-keys
7. Create new API key
8. Copy the key

### Google Gemini (Fallback - FREE)

1. Go to: https://aistudio.google.com/
2. Sign in with Google
3. Click "Get API Key"
4. Create API key
5. Copy the key

---

## Step 2: Add API Keys to .env

Open your `.env` file and add these lines:

```env
MISTRAL_API_KEY=your_mistral_key_here
GEMINI_API_KEY=your_gemini_key_here
```

---

## Step 3: Install Dependencies

Run the installation script:

```bash
python install_dependencies.py
```

This will install:
- mistralai (AI client)
- google-generativeai (fallback AI)
- sentence-transformers (semantic matching)
- python-docx (resume generation)
- Other required packages

---

## Step 4: Create New Database Tables

Run the migration script:

```bash
python create_new_tables.py
```

This creates two new tables:
- `job_matches` - Stores AI match analysis
- `custom_resumes` - Stores generated resumes

**Your existing tables are NOT modified!**

---

## Step 5: Test the Setup

### Test 1: AI Client

```python
from ai.multi_provider_client import ai_client

response = ai_client.chat_complete(
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response)
```

Expected: A greeting from Mistral or Gemini

### Test 2: Job Matcher

```python
from agents.job_matcher.matcher import job_matcher

resume = {
    'skills': ['Python', 'FastAPI', 'React'],
    'experience_years': 3
}

job = {
    'title': 'Full Stack Developer',
    'description': 'Looking for Python and React developer'
}

result = job_matcher.calculate_match_score(resume, job)
print(f"Match Score: {result['overall_score']}%")
```

Expected: Match score around 70-90%

### Test 3: Resume Generator

```python
from agents.resume_generator.generator import resume_generator

resume = {
    'name': 'John Doe',
    'email': 'john@example.com',
    'skills': ['Python', 'React'],
    'experience': 'Built web applications'
}

job = {
    'id': 1,
    'title': 'Developer',
    'company': 'Tech Corp'
}

match = {'matched_skills': ['Python'], 'missing_skills': []}

filename = resume_generator.generate_custom_resume(resume, job, match)
print(f"Resume created: {filename}")
```

Expected: DOCX file created in `generated_resumes/` folder

---

## Step 6: Start the Server

```bash
python -m uvicorn api.main:app --reload
```

Server starts at: http://localhost:8000

---

## Step 7: Test New API Endpoints

### Analyze Job Match

```bash
curl -X POST http://localhost:8000/jobs/1/analyze
```

Returns:
```json
{
  "overall_score": 85.5,
  "skill_score": 90.0,
  "matched_skills": ["Python", "React"],
  "missing_skills": ["Docker"],
  "why_good_fit": "You're an excellent match..."
}
```

### Generate Custom Resume

```bash
curl -X POST http://localhost:8000/jobs/1/generate-resume
```

Returns:
```json
{
  "message": "Resume generated successfully",
  "filename": "generated_resumes/resume_TechCorp_1.docx",
  "download_url": "/download-resume/1"
}
```

### Download Resume

```bash
curl http://localhost:8000/download-resume/1 --output resume.docx
```

Downloads the custom resume file.

---

## Step 8: Update Frontend (Optional)

The new endpoints work with your existing dashboard. To add UI enhancements:

1. Open `frontend/public/dashboard.html`
2. Add "Analyze Match" and "Generate Resume" buttons to job cards
3. Display match scores with color-coded badges

See `Project_steps.md` Step 1.6 for detailed frontend code.

---

## Troubleshooting

### Error: "Rate limited on all providers"

**Solution:** Wait 60 seconds. Free tiers have rate limits:
- Mistral: 2 requests/minute
- Gemini: 15 requests/minute

### Error: "No resume found"

**Solution:** Upload a resume first via the chat interface or `/resume/parse` endpoint.

### Error: "Module not found"

**Solution:** Run `python install_dependencies.py` again.

### Error: "Table already exists"

**Solution:** This is normal! The script skips existing tables.

---

## What's Next?

Your enhanced job matching is now ready! The system will:

1. **Analyze jobs** - Calculate match scores automatically
2. **Generate resumes** - Create tailored resumes per job
3. **Provide insights** - Show skill gaps and fit explanations

**Your existing workflow continues working normally!**

---

## Need Help?

Check these files:
- `Project_steps.md` - Detailed implementation steps
- `project_goal.md` - Complete feature roadmap
- `Project_status.md` - Current system documentation

---

*Setup complete! Your AI-powered job matching is ready to use.* 🚀
