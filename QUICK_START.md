# Quick Start: Enhanced Job Matching

Get your AI-powered job matching running in 5 minutes!

## 🚀 Quick Setup (5 Steps)

### 1. Install Dependencies (2 min)

```bash
python install_dependencies.py
```

### 2. Get Free API Keys (2 min)

**Mistral AI:**
- Go to: https://console.mistral.ai/
- Sign up → Activate "Experiment" plan (free)
- Get API key from: https://console.mistral.ai/api-keys

**Google Gemini (optional fallback):**
- Go to: https://aistudio.google.com/
- Get API key

### 3. Add Keys to .env (30 sec)

```env
MISTRAL_API_KEY=your_mistral_key_here
GEMINI_API_KEY=your_gemini_key_here
```

### 4. Create Database Tables (10 sec)

```bash
python create_new_tables.py
```

### 5. Test Everything (30 sec)

```bash
python test_enhanced_features.py
```

---

## ✅ You're Done!

Start the server:

```bash
python -m uvicorn api.main:app --reload
```

---

## 🎯 Try It Out

### Test 1: Analyze a Job

```bash
curl -X POST http://localhost:8000/jobs/1/analyze
```

### Test 2: Generate Custom Resume

```bash
curl -X POST http://localhost:8000/jobs/1/generate-resume
```

### Test 3: Download Resume

```bash
curl http://localhost:8000/download-resume/1 --output resume.docx
```

---

## 📊 What You Get

✅ **AI Match Scores** - See how well you match each job (0-100%)
✅ **Skill Gap Analysis** - Know exactly what skills you're missing
✅ **Custom Resumes** - Tailored resume for each job (ATS-optimized)
✅ **Fit Explanations** - AI tells you why you're a good match

---

## 🔥 Next Steps

1. **Upload your resume** via chat interface
2. **Search for jobs** (existing workflow works!)
3. **Click "Analyze Match"** on any job
4. **Generate custom resume** for high-match jobs
5. **Download and apply!**

---

## 💡 Pro Tips

- **Mistral free tier:** 2 requests/minute (pace your requests)
- **Gemini fallback:** Kicks in automatically if Mistral is rate-limited
- **Combined capacity:** ~4,000 requests/day for free!

---

## ❓ Need Help?

- **Setup issues?** Check `SETUP_GUIDE.md`
- **Detailed steps?** See `Project_steps.md`
- **Full roadmap?** Read `project_goal.md`

---

**Your existing system still works perfectly!**
**New features are additive, not destructive.** ✨
