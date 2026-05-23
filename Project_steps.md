# Project Implementation Steps: Transform into Agentic Job Application System

## Overview

This document provides **DETAILED, STEP-BY-STEP** instructions to transform your current job scraping system into a complete AI-powered agentic job application platform. Follow these steps sequentially, and you can continue even if I run out of credits.

---

## Table of Contents

1. [Prerequisites & Setup](#prerequisites--setup)
2. [Phase 1: Enhanced Job Matching & Personalization](#phase-1-enhanced-job-matching--personalization)
3. [Phase 2: Vision-Guided Adaptive Scraping](#phase-2-vision-guided-adaptive-scraping)
4. [Phase 3: Recruiter Intelligence](#phase-3-recruiter-intelligence)
5. [Phase 4: Outreach Automation](#phase-4-outreach-automation)
6. [Phase 5: Auto-Apply Agent](#phase-5-auto-apply-agent)
7. [Testing & Deployment](#testing--deployment)
8. [Troubleshooting Guide](#troubleshooting-guide)

---

## Prerequisites & Setup

### Step 1: Set Up Mistral AI Experiment Plan (FREE)

**Time:** 10 minutes

**Instructions:**

1. **Go to Mistral AI Console**
   - Open browser: https://console.mistral.ai/
   - Click "Sign Up" or "Sign In"

2. **Create Account**
   - Use your email and password
   - Verify email address

3. **Activate Experiment Plan**
   - Go to: https://console.mistral.ai/upgrade/plans
   - Click "Experiment for free"
   - Enter phone number for verification
   - Accept Terms of Service
   - Click "Subscribe"

4. **Generate API Key**
   - Go to: https://console.mistral.ai/api-keys
   - Click "Create new key"
   - Name: "Job Agent API Key"
   - Copy the API key (starts with "...")
   - Save it securely

5. **Add to .env File**
   ```bash
   # Open .env file in your project
   # Add this line:
   MISTRAL_API_KEY=your_api_key_here
   ```

**Verification:**
```python
# Test the API key
from mistralai import Mistral

client = Mistral(api_key="your_api_key_here")
response = client.chat.complete(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

**Expected Output:** A greeting response from Mistral

---

### Step 2: Set Up Google Gemini API (FREE - Fallback)

**Time:** 10 minutes

**Instructions:**

1. **Go to Google AI Studio**
   - Open browser: https://aistudio.google.com/
   - Sign in with Google account

2. **Get API Key**
   - Click "Get API Key" button
   - Click "Create API Key"
   - Copy the API key
   - Save it securely

3. **Add to .env File**
   ```bash
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

**Verification:**
```python
import google.generativeai as genai

genai.configure(api_key="your_gemini_api_key_here")
model = genai.GenerativeModel('gemini-2.5-flash')
response = model.generate_content("Hello!")
print(response.text)
```

**Expected Output:** A greeting response from Gemini

---

### Step 3: Install Required Python Packages

**Time:** 5 minutes

**Instructions:**

1. **Open terminal in project directory**
   ```bash
   cd "c:\Harshith Games\Project"
   ```

2. **Install new packages**
   ```bash
   pip install mistralai
   pip install google-generativeai
   pip install sentence-transformers
   pip install python-docx
   pip install reportlab
   pip install pyautogui
   pip install pillow
   pip install opencv-python
   ```

3. **Update requirements.txt**
   ```bash
   pip freeze > requirements.txt
   ```

**Verification:**
```python
# Test imports
import mistralai
import google.generativeai
from sentence_transformers import SentenceTransformer
import pyautogui
print("All packages installed successfully!")
```

---


## Phase 1: Enhanced Job Matching & Personalization

### Overview
Build intelligent job matching that goes beyond keyword matching. This phase adds:
- Deep semantic similarity analysis
- Skill gap identification
- Custom resume generation per job
- AI-generated "why you're a good fit" pitch

**Time Estimate:** 2-3 weeks
**Difficulty:** Medium
**Value:** ⭐⭐⭐⭐⭐ (Highest impact)

---

### Step 1.1: Create AI Client Wrapper

**Time:** 30 minutes

**File:** `ai/multi_provider_client.py`

**Instructions:**

1. **Create the file**
   ```bash
   # File already exists at ai/ai_client.py
   # We'll create a new one for multi-provider support
   ```

2. **Write the code:**

```python
"""
Multi-provider AI client with automatic fallback
Supports: Mistral (primary), Gemini (fallback)
"""

import os
import time
from typing import Optional, Dict, Any, List
from mistralai import Mistral
import google.generativeai as genai

class MultiProviderAIClient:
    def __init__(self):
        # Initialize Mistral
        self.mistral_key = os.getenv("MISTRAL_API_KEY")
        self.mistral_client = Mistral(api_key=self.mistral_key) if self.mistral_key else None
        
        # Initialize Gemini
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
        
        # Rate limiting
        self.mistral_limit = {"rpm": 2, "requests": [], "last_reset": time.time()}
        self.gemini_limit = {"rpm": 15, "requests": [], "last_reset": time.time()}
    
    def _check_rate_limit(self, provider: str) -> bool:
        """Check if we can make a request to this provider"""
        limit_info = self.mistral_limit if provider == "mistral" else self.gemini_limit
        current_time = time.time()
        
        # Reset if minute has passed
        if current_time - limit_info["last_reset"] >= 60:
            limit_info["requests"] = []
            limit_info["last_reset"] = current_time
        
        # Remove requests older than 1 minute
        limit_info["requests"] = [
            req_time for req_time in limit_info["requests"]
            if current_time - req_time < 60
        ]
        
        # Check if under limit
        return len(limit_info["requests"]) < limit_info["rpm"]
    
    def _record_request(self, provider: str):
        """Record that we made a request"""
        limit_info = self.mistral_limit if provider == "mistral" else self.gemini_limit
        limit_info["requests"].append(time.time())
    
    def chat_complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Send chat completion request with automatic provider fallback
        """
        # Try Mistral first
        if self.mistral_client and self._check_rate_limit("mistral"):
            try:
                response = self.mistral_client.chat.complete(
                    model=model or "mistral-large-latest",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                self._record_request("mistral")
                return response.choices[0].message.content
            except Exception as e:
                print(f"Mistral error: {e}, falling back to Gemini")
        
        # Fallback to Gemini
        if self.gemini_key and self._check_rate_limit("gemini"):
            try:
                model_obj = genai.GenerativeModel('gemini-2.5-flash')
                # Convert messages to Gemini format
                prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                response = model_obj.generate_content(prompt)
                self._record_request("gemini")
                return response.text
            except Exception as e:
                print(f"Gemini error: {e}")
                raise Exception("All AI providers failed")
        
        # If we get here, we're rate limited
        raise Exception("Rate limited on all providers. Please wait 60 seconds.")

# Global instance
ai_client = MultiProviderAIClient()
```

3. **Test the client:**

```python
# Test file: test_ai_client.py
from ai.multi_provider_client import ai_client

response = ai_client.chat_complete(
    messages=[{"role": "user", "content": "Say hello!"}]
)
print(response)
```

**Expected Output:** A greeting from either Mistral or Gemini

---


### Step 1.2: Build Semantic Job Matcher

**Time:** 2 hours

**File:** `agents/job_matcher/matcher.py`

**Instructions:**

1. **Create directory structure**
   ```bash
   mkdir agents\job_matcher
   type nul > agents\job_matcher\__init__.py
   ```

2. **Create the matcher:**

```python
"""
Semantic job matching using embeddings and AI analysis
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Dict, List, Tuple
from ai.multi_provider_client import ai_client

class JobMatcher:
    def __init__(self):
        # Load embedding model (runs locally, free)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def calculate_match_score(
        self,
        resume_data: Dict,
        job_data: Dict
    ) -> Dict:
        """
        Calculate comprehensive match score between resume and job
        
        Returns:
            {
                'overall_score': 0-100,
                'skill_score': 0-100,
                'experience_score': 0-100,
                'education_score': 0-100,
                'matched_skills': [...],
                'missing_skills': [...],
                'why_good_fit': "AI-generated explanation"
            }
        """
        # Extract text for embedding
        resume_text = self._extract_resume_text(resume_data)
        job_text = self._extract_job_text(job_data)
        
        # Calculate semantic similarity
        resume_embedding = self.model.encode(resume_text)
        job_embedding = self.model.encode(job_text)
        semantic_similarity = np.dot(resume_embedding, job_embedding) / (
            np.linalg.norm(resume_embedding) * np.linalg.norm(job_embedding)
        )
        
        # Calculate component scores
        skill_score = self._calculate_skill_score(resume_data, job_data)
        experience_score = self._calculate_experience_score(resume_data, job_data)
        education_score = self._calculate_education_score(resume_data, job_data)
        
        # Weighted overall score
        overall_score = (
            semantic_similarity * 30 +
            skill_score * 40 +
            experience_score * 20 +
            education_score * 10
        )
        
        # Identify matched and missing skills
        matched_skills, missing_skills = self._analyze_skills(resume_data, job_data)
        
        # Generate AI explanation
        why_good_fit = self._generate_fit_explanation(
            resume_data, job_data, overall_score, matched_skills, missing_skills
        )
        
        return {
            'overall_score': round(overall_score, 2),
            'skill_score': round(skill_score, 2),
            'experience_score': round(experience_score, 2),
            'education_score': round(education_score, 2),
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'why_good_fit': why_good_fit
        }
    
    def _extract_resume_text(self, resume_data: Dict) -> str:
        """Combine all resume fields into searchable text"""
        parts = []
        if 'skills' in resume_data:
            parts.append(f"Skills: {', '.join(resume_data['skills'])}")
        if 'experience' in resume_data:
            parts.append(f"Experience: {resume_data['experience']}")
        if 'education' in resume_data:
            parts.append(f"Education: {resume_data['education']}")
        return " ".join(parts)
    
    def _extract_job_text(self, job_data: Dict) -> str:
        """Combine job fields into searchable text"""
        parts = [
            job_data.get('title', ''),
            job_data.get('description', ''),
            job_data.get('requirements', '')
        ]
        return " ".join(parts)
    
    def _calculate_skill_score(self, resume_data: Dict, job_data: Dict) -> float:
        """Calculate skill match percentage"""
        resume_skills = set(s.lower() for s in resume_data.get('skills', []))
        job_skills = self._extract_job_skills(job_data)
        
        if not job_skills:
            return 50.0  # Neutral score if no skills listed
        
        matched = resume_skills.intersection(job_skills)
        return (len(matched) / len(job_skills)) * 100
    
    def _calculate_experience_score(self, resume_data: Dict, job_data: Dict) -> float:
        """Calculate experience match"""
        resume_years = resume_data.get('experience_years', 0)
        required_years = self._extract_required_experience(job_data)
        
        if required_years == 0:
            return 100.0  # No requirement
        
        if resume_years >= required_years:
            return 100.0
        elif resume_years >= required_years * 0.7:
            return 80.0
        elif resume_years >= required_years * 0.5:
            return 60.0
        else:
            return 40.0
    
    def _calculate_education_score(self, resume_data: Dict, job_data: Dict) -> float:
        """Calculate education match"""
        # Simplified - can be enhanced
        return 75.0
    
    def _extract_job_skills(self, job_data: Dict) -> set:
        """Extract skills from job description"""
        # Use AI to extract skills
        prompt = f"""
        Extract technical skills from this job description.
        Return ONLY a comma-separated list of skills.
        
        Job: {job_data.get('title', '')}
        Description: {job_data.get('description', '')[:500]}
        
        Skills:
        """
        
        try:
            response = ai_client.chat_complete(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            skills = [s.strip().lower() for s in response.split(',')]
            return set(skills)
        except:
            return set()
    
    def _extract_required_experience(self, job_data: Dict) -> int:
        """Extract required years of experience"""
        description = job_data.get('description', '').lower()
        
        # Look for patterns like "3+ years", "5 years experience"
        import re
        patterns = [
            r'(\d+)\+?\s*years?',
            r'(\d+)\s*yrs?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                return int(match.group(1))
        
        return 0
    
    def _analyze_skills(self, resume_data: Dict, job_data: Dict) -> Tuple[List, List]:
        """Identify matched and missing skills"""
        resume_skills = set(s.lower() for s in resume_data.get('skills', []))
        job_skills = self._extract_job_skills(job_data)
        
        matched = list(resume_skills.intersection(job_skills))
        missing = list(job_skills - resume_skills)
        
        return matched, missing
    
    def _generate_fit_explanation(
        self,
        resume_data: Dict,
        job_data: Dict,
        score: float,
        matched_skills: List,
        missing_skills: List
    ) -> str:
        """Generate AI explanation of why candidate is a good fit"""
        prompt = f"""
        Write a concise 2-3 sentence explanation of why this candidate is a good fit for this job.
        Focus on strengths and matched skills. Be encouraging but honest.
        
        Job: {job_data.get('title', '')}
        Company: {job_data.get('company', '')}
        
        Candidate Skills: {', '.join(resume_data.get('skills', [])[:10])}
        Matched Skills: {', '.join(matched_skills[:5])}
        Missing Skills: {', '.join(missing_skills[:3])}
        Match Score: {score:.0f}%
        
        Explanation:
        """
        
        try:
            return ai_client.chat_complete(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
        except:
            return f"You have a {score:.0f}% match with this position based on your skills and experience."

# Global instance
job_matcher = JobMatcher()
```

3. **Test the matcher:**

```python
# test_matcher.py
from agents.job_matcher.matcher import job_matcher

resume = {
    'skills': ['Python', 'FastAPI', 'React', 'SQL'],
    'experience_years': 3,
    'education': 'BS Computer Science'
}

job = {
    'title': 'Full Stack Developer',
    'company': 'Tech Corp',
    'description': 'Looking for a developer with Python, React, and 2+ years experience',
    'requirements': 'Python, React, SQL, 2 years experience'
}

result = job_matcher.calculate_match_score(resume, job)
print(f"Match Score: {result['overall_score']}%")
print(f"Matched Skills: {result['matched_skills']}")
print(f"Missing Skills: {result['missing_skills']}")
print(f"Why Good Fit: {result['why_good_fit']}")
```

**Expected Output:**
```
Match Score: 85.5%
Matched Skills: ['python', 'react', 'sql']
Missing Skills: []
Why Good Fit: You're an excellent match for this Full Stack Developer role...
```

---


### Step 1.3: Build Custom Resume Generator

**Time:** 3 hours

**File:** `agents/resume_generator/generator.py`

**Instructions:**

1. **Create directory**
   ```bash
   mkdir agents\resume_generator
   type nul > agents\resume_generator\__init__.py
   ```

2. **Create the generator:**

```python
"""
Custom resume generator - creates tailored resumes for each job
"""

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from typing import Dict
from ai.multi_provider_client import ai_client
import os

class ResumeGenerator:
    def __init__(self):
        self.output_dir = "generated_resumes"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_custom_resume(
        self,
        resume_data: Dict,
        job_data: Dict,
        match_data: Dict
    ) -> str:
        """
        Generate a custom resume tailored to specific job
        
        Returns: Path to generated DOCX file
        """
        # Use AI to rewrite resume sections
        optimized_summary = self._generate_summary(resume_data, job_data)
        optimized_experience = self._optimize_experience(resume_data, job_data)
        optimized_skills = self._prioritize_skills(resume_data, job_data, match_data)
        
        # Create DOCX
        doc = Document()
        
        # Header - Name and Contact
        self._add_header(doc, resume_data)
        
        # Professional Summary
        self._add_section(doc, "Professional Summary", optimized_summary)
        
        # Skills (prioritized for this job)
        self._add_section(doc, "Technical Skills", optimized_skills)
        
        # Experience (reordered and rewritten)
        self._add_section(doc, "Professional Experience", optimized_experience)
        
        # Education
        self._add_section(doc, "Education", resume_data.get('education', ''))
        
        # Save
        filename = f"{self.output_dir}/resume_{job_data.get('company', 'company')}_{job_data.get('id', 'job')}.docx"
        doc.save(filename)
        
        return filename
    
    def _generate_summary(self, resume_data: Dict, job_data: Dict) -> str:
        """Generate tailored professional summary"""
        prompt = f"""
        Write a professional summary (3-4 sentences) for a resume tailored to this job.
        Highlight relevant skills and experience. Be specific and quantifiable.
        
        Candidate Background:
        - Skills: {', '.join(resume_data.get('skills', [])[:10])}
        - Experience: {resume_data.get('experience_years', 0)} years
        - Current Role: {resume_data.get('current_role', 'Professional')}
        
        Target Job:
        - Title: {job_data.get('title', '')}
        - Company: {job_data.get('company', '')}
        - Key Requirements: {job_data.get('requirements', '')[:200]}
        
        Professional Summary:
        """
        
        try:
            return ai_client.chat_complete(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
        except:
            return f"Experienced professional with {resume_data.get('experience_years', 0)} years in the field."
    
    def _optimize_experience(self, resume_data: Dict, job_data: Dict) -> str:
        """Rewrite experience section to highlight relevant achievements"""
        original_experience = resume_data.get('experience', '')
        
        prompt = f"""
        Rewrite this work experience to emphasize skills relevant to the target job.
        Use action verbs and quantify achievements. Keep it concise.
        
        Original Experience:
        {original_experience[:1000]}
        
        Target Job: {job_data.get('title', '')}
        Key Skills Needed: {job_data.get('requirements', '')[:200]}
        
        Optimized Experience:
        """
        
        try:
            return ai_client.chat_complete(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
        except:
            return original_experience
    
    def _prioritize_skills(self, resume_data: Dict, job_data: Dict, match_data: Dict) -> str:
        """Reorder skills to put matched skills first"""
        matched = match_data.get('matched_skills', [])
        all_skills = resume_data.get('skills', [])
        
        # Put matched skills first
        prioritized = matched + [s for s in all_skills if s.lower() not in [m.lower() for m in matched]]
        
        # Group by category (optional enhancement)
        return ", ".join(prioritized[:15])  # Limit to top 15
    
    def _add_header(self, doc: Document, resume_data: Dict):
        """Add name and contact info header"""
        # Name
        name_para = doc.add_paragraph()
        name_run = name_para.add_run(resume_data.get('name', 'Your Name'))
        name_run.font.size = Pt(18)
        name_run.font.bold = True
        name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Contact
        contact_para = doc.add_paragraph()
        contact_text = f"{resume_data.get('email', '')} | {resume_data.get('phone', '')} | {resume_data.get('location', '')}"
        contact_run = contact_para.add_run(contact_text)
        contact_run.font.size = Pt(10)
        contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph()  # Spacing
    
    def _add_section(self, doc: Document, title: str, content: str):
        """Add a section with title and content"""
        # Section title
        title_para = doc.add_paragraph()
        title_run = title_para.add_run(title.upper())
        title_run.font.size = Pt(12)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(0, 0, 128)  # Dark blue
        
        # Horizontal line
        doc.add_paragraph('_' * 80)
        
        # Content
        content_para = doc.add_paragraph(content)
        content_para.style = 'Normal'
        
        doc.add_paragraph()  # Spacing

# Global instance
resume_generator = ResumeGenerator()
```

3. **Test the generator:**

```python
# test_resume_generator.py
from agents.resume_generator.generator import resume_generator

resume = {
    'name': 'John Doe',
    'email': 'john@example.com',
    'phone': '+1234567890',
    'location': 'San Francisco, CA',
    'skills': ['Python', 'FastAPI', 'React', 'SQL', 'Docker'],
    'experience_years': 3,
    'current_role': 'Software Engineer',
    'experience': 'Built REST APIs using FastAPI. Developed React frontends. Managed PostgreSQL databases.',
    'education': 'BS Computer Science, Stanford University, 2020'
}

job = {
    'id': 123,
    'title': 'Senior Full Stack Developer',
    'company': 'Tech Corp',
    'requirements': 'Python, React, SQL, 3+ years experience',
    'description': 'We need a full stack developer...'
}

match = {
    'matched_skills': ['Python', 'React', 'SQL'],
    'missing_skills': []
}

filename = resume_generator.generate_custom_resume(resume, job, match)
print(f"Resume generated: {filename}")
```

**Expected Output:**
```
Resume generated: generated_resumes/resume_Tech_Corp_123.docx
```

Open the file to verify it looks professional!

---


### Step 1.4: Update Database Schema

**Time:** 30 minutes

**File:** `database/models.py`

**Instructions:**

1. **Add new tables to models.py:**

```python
# Add these new models to your existing models.py

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

# Add to existing models:

class JobMatch(Base):
    __tablename__ = "job_matches"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Scores
    overall_score = Column(Float)
    skill_score = Column(Float)
    experience_score = Column(Float)
    education_score = Column(Float)
    
    # Analysis
    matched_skills = Column(Text)  # JSON array as string
    missing_skills = Column(Text)  # JSON array as string
    why_good_fit = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="matches")
    user = relationship("User", back_populates="job_matches")


class CustomResume(Base):
    __tablename__ = "custom_resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Resume content
    resume_text = Column(Text)
    resume_pdf_path = Column(String)
    resume_docx_path = Column(String)
    
    # Metadata
    ats_optimized = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="custom_resumes")
    user = relationship("User", back_populates="custom_resumes")


# Update existing Job model to add relationships:
# Add these lines to your Job class:
# matches = relationship("JobMatch", back_populates="job")
# custom_resumes = relationship("CustomResume", back_populates="job")

# Update existing User model to add relationships:
# Add these lines to your User class:
# job_matches = relationship("JobMatch", back_populates="user")
# custom_resumes = relationship("CustomResume", back_populates="user")
```

2. **Create migration script:**

```python
# create_tables.py
from database.engine import engine
from database.models import Base

# Create all tables
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")
```

3. **Run migration:**

```bash
python create_tables.py
```

**Expected Output:**
```
Tables created successfully!
```

---

### Step 1.5: Create API Endpoints

**Time:** 1 hour

**File:** `api/main.py`

**Instructions:**

1. **Add new endpoints to main.py:**

```python
# Add these imports at the top
from agents.job_matcher.matcher import job_matcher
from agents.resume_generator.generator import resume_generator
from database.models import JobMatch, CustomResume
import json

# Add these new endpoints:

@app.post("/jobs/{job_id}/analyze")
async def analyze_job_match(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Analyze how well user's resume matches this job
    """
    # Get job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get user's latest resume (simplified - should use auth)
    resume = db.query(Resume).order_by(Resume.created_at.desc()).first()
    if not resume:
        raise HTTPException(status_code=404, detail="No resume found")
    
    # Prepare data
    resume_data = {
        'skills': json.loads(resume.skills) if resume.skills else [],
        'experience_years': resume.experience_years or 0,
        'education': resume.text_content[:500] if resume.text_content else '',
        'name': resume.filename,
        'email': 'user@example.com',  # Should come from user profile
        'phone': '',
        'location': ''
    }
    
    job_data = {
        'id': job.id,
        'title': job.title,
        'company': job.company,
        'description': job.description or '',
        'requirements': job.requirements or ''
    }
    
    # Calculate match
    match_result = job_matcher.calculate_match_score(resume_data, job_data)
    
    # Save to database
    job_match = JobMatch(
        job_id=job_id,
        user_id=1,  # Should use actual user ID from auth
        overall_score=match_result['overall_score'],
        skill_score=match_result['skill_score'],
        experience_score=match_result['experience_score'],
        education_score=match_result['education_score'],
        matched_skills=json.dumps(match_result['matched_skills']),
        missing_skills=json.dumps(match_result['missing_skills']),
        why_good_fit=match_result['why_good_fit']
    )
    db.add(job_match)
    db.commit()
    
    return match_result


@app.post("/jobs/{job_id}/generate-resume")
async def generate_custom_resume(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate custom resume for this job
    """
    # Get job and match
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_match = db.query(JobMatch).filter(JobMatch.job_id == job_id).first()
    if not job_match:
        raise HTTPException(status_code=404, detail="Analyze job first")
    
    # Get resume
    resume = db.query(Resume).order_by(Resume.created_at.desc()).first()
    if not resume:
        raise HTTPException(status_code=404, detail="No resume found")
    
    # Prepare data
    resume_data = {
        'name': 'John Doe',  # Should come from user profile
        'email': 'user@example.com',
        'phone': '+1234567890',
        'location': 'City, State',
        'skills': json.loads(resume.skills) if resume.skills else [],
        'experience_years': resume.experience_years or 0,
        'current_role': 'Professional',
        'experience': resume.text_content[:1000] if resume.text_content else '',
        'education': 'Your Education'
    }
    
    job_data = {
        'id': job.id,
        'title': job.title,
        'company': job.company,
        'description': job.description or '',
        'requirements': job.requirements or ''
    }
    
    match_data = {
        'matched_skills': json.loads(job_match.matched_skills),
        'missing_skills': json.loads(job_match.missing_skills)
    }
    
    # Generate resume
    filename = resume_generator.generate_custom_resume(resume_data, job_data, match_data)
    
    # Save to database
    custom_resume = CustomResume(
        job_id=job_id,
        user_id=1,
        resume_docx_path=filename,
        ats_optimized=True
    )
    db.add(custom_resume)
    db.commit()
    
    return {
        "message": "Resume generated successfully",
        "filename": filename,
        "download_url": f"/download-resume/{custom_resume.id}"
    }


@app.get("/download-resume/{resume_id}")
async def download_custom_resume(resume_id: int, db: Session = Depends(get_db)):
    """
    Download generated custom resume
    """
    custom_resume = db.query(CustomResume).filter(CustomResume.id == resume_id).first()
    if not custom_resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        custom_resume.resume_docx_path,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        filename=f"resume_{custom_resume.job_id}.docx"
    )
```

2. **Test the endpoints:**

```bash
# Start server
python -m uvicorn api.main:app --reload

# In another terminal or Postman:
# 1. Analyze a job
curl -X POST http://localhost:8000/jobs/1/analyze

# 2. Generate custom resume
curl -X POST http://localhost:8000/jobs/1/generate-resume

# 3. Download resume
curl http://localhost:8000/download-resume/1 --output resume.docx
```

**Expected Output:**
- Analyze: JSON with match scores
- Generate: Success message with filename
- Download: DOCX file downloaded

---


### Step 1.6: Update Frontend Dashboard

**Time:** 2 hours

**File:** `frontend/public/dashboard.html`

**Instructions:**

1. **Add match score display to job cards:**

Find the job card rendering section and update it:

```javascript
// In dashboard.html, find the renderJobs function and update:

function renderJobs(jobs) {
    const container = document.getElementById('jobs-container');
    container.innerHTML = '';
    
    jobs.forEach(job => {
        const card = document.createElement('div');
        card.className = 'job-card';
        
        // Add match score badge
        const matchBadge = getMatchBadge(job.match_score);
        
        card.innerHTML = `
            <div class="job-header">
                <h3>${job.title}</h3>
                ${matchBadge}
            </div>
            <p class="company">${job.company}</p>
            <p class="location">${job.location}</p>
            
            <!-- Match Details -->
            <div class="match-details">
                <div class="match-bar">
                    <div class="match-fill" style="width: ${job.match_score || 0}%"></div>
                </div>
                <p class="match-text">${job.match_score || 0}% Match</p>
            </div>
            
            <!-- Skill Gap -->
            ${job.missing_skills && job.missing_skills.length > 0 ? `
                <div class="skill-gap">
                    <span class="gap-icon">⚠️</span>
                    Missing ${job.missing_skills.length} skills: 
                    ${job.missing_skills.slice(0, 3).join(', ')}
                </div>
            ` : ''}
            
            <!-- Why Good Fit -->
            ${job.why_good_fit ? `
                <div class="good-fit">
                    <p><strong>Why you're a good fit:</strong></p>
                    <p>${job.why_good_fit}</p>
                </div>
            ` : ''}
            
            <!-- Actions -->
            <div class="job-actions">
                <button onclick="analyzeJob(${job.id})" class="btn-analyze">
                    Analyze Match
                </button>
                <button onclick="generateResume(${job.id})" class="btn-resume">
                    Generate Resume
                </button>
                <button onclick="viewJob(${job.id})" class="btn-view">
                    View Details
                </button>
            </div>
        `;
        
        container.appendChild(card);
    });
}

function getMatchBadge(score) {
    if (!score) return '';
    
    let color, label;
    if (score >= 90) {
        color = '#10b981'; // Green
        label = 'Excellent';
    } else if (score >= 70) {
        color = '#3b82f6'; // Blue
        label = 'Good';
    } else if (score >= 50) {
        color = '#f59e0b'; // Orange
        label = 'Fair';
    } else {
        color = '#ef4444'; // Red
        label = 'Poor';
    }
    
    return `
        <span class="match-badge" style="background-color: ${color}">
            ${label} (${score}%)
        </span>
    `;
}

// Add these new functions:

async function analyzeJob(jobId) {
    try {
        showLoading('Analyzing job match...');
        
        const response = await fetch(`/jobs/${jobId}/analyze`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Analysis failed');
        
        const result = await response.json();
        
        hideLoading();
        showMatchResults(result);
        
        // Refresh jobs to show updated match
        loadJobs();
        
    } catch (error) {
        hideLoading();
        alert('Error analyzing job: ' + error.message);
    }
}

async function generateResume(jobId) {
    try {
        showLoading('Generating custom resume...');
        
        const response = await fetch(`/jobs/${jobId}/generate-resume`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Generation failed');
        
        const result = await response.json();
        
        hideLoading();
        
        // Show success and download link
        alert('Resume generated successfully!');
        window.open(result.download_url, '_blank');
        
    } catch (error) {
        hideLoading();
        alert('Error generating resume: ' + error.message);
    }
}

function showMatchResults(result) {
    // Create modal to show detailed match results
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close" onclick="this.parentElement.parentElement.remove()">&times;</span>
            <h2>Match Analysis</h2>
            
            <div class="score-grid">
                <div class="score-item">
                    <h3>Overall</h3>
                    <div class="score-circle">${result.overall_score}%</div>
                </div>
                <div class="score-item">
                    <h3>Skills</h3>
                    <div class="score-circle">${result.skill_score}%</div>
                </div>
                <div class="score-item">
                    <h3>Experience</h3>
                    <div class="score-circle">${result.experience_score}%</div>
                </div>
                <div class="score-item">
                    <h3>Education</h3>
                    <div class="score-circle">${result.education_score}%</div>
                </div>
            </div>
            
            <div class="skills-section">
                <h3>✅ Matched Skills</h3>
                <div class="skill-tags">
                    ${result.matched_skills.map(s => `<span class="skill-tag matched">${s}</span>`).join('')}
                </div>
            </div>
            
            ${result.missing_skills.length > 0 ? `
                <div class="skills-section">
                    <h3>⚠️ Missing Skills</h3>
                    <div class="skill-tags">
                        ${result.missing_skills.map(s => `<span class="skill-tag missing">${s}</span>`).join('')}
                    </div>
                </div>
            ` : ''}
            
            <div class="fit-section">
                <h3>💡 Why You're a Good Fit</h3>
                <p>${result.why_good_fit}</p>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function showLoading(message) {
    const loader = document.createElement('div');
    loader.id = 'loader';
    loader.innerHTML = `
        <div class="loader-content">
            <div class="spinner"></div>
            <p>${message}</p>
        </div>
    `;
    document.body.appendChild(loader);
}

function hideLoading() {
    const loader = document.getElementById('loader');
    if (loader) loader.remove();
}
```

2. **Add CSS styles:**

```css
/* Add to dashboard.html <style> section */

.match-details {
    margin: 15px 0;
}

.match-bar {
    width: 100%;
    height: 8px;
    background-color: #e5e7eb;
    border-radius: 4px;
    overflow: hidden;
}

.match-fill {
    height: 100%;
    background: linear-gradient(90deg, #3b82f6, #10b981);
    transition: width 0.3s ease;
}

.match-text {
    margin-top: 5px;
    font-size: 14px;
    color: #6b7280;
}

.match-badge {
    padding: 4px 12px;
    border-radius: 12px;
    color: white;
    font-size: 12px;
    font-weight: bold;
}

.skill-gap {
    background-color: #fef3c7;
    border-left: 4px solid #f59e0b;
    padding: 10px;
    margin: 10px 0;
    font-size: 14px;
}

.gap-icon {
    margin-right: 5px;
}

.good-fit {
    background-color: #f0fdf4;
    border-left: 4px solid #10b981;
    padding: 10px;
    margin: 10px 0;
    font-size: 14px;
}

.job-actions {
    display: flex;
    gap: 10px;
    margin-top: 15px;
}

.btn-analyze, .btn-resume, .btn-view {
    flex: 1;
    padding: 8px 12px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
}

.btn-analyze {
    background-color: #3b82f6;
    color: white;
}

.btn-analyze:hover {
    background-color: #2563eb;
}

.btn-resume {
    background-color: #10b981;
    color: white;
}

.btn-resume:hover {
    background-color: #059669;
}

.btn-view {
    background-color: #6b7280;
    color: white;
}

.btn-view:hover {
    background-color: #4b5563;
}

/* Modal styles */
.modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal-content {
    background-color: white;
    padding: 30px;
    border-radius: 12px;
    max-width: 600px;
    max-height: 80vh;
    overflow-y: auto;
    position: relative;
}

.close {
    position: absolute;
    top: 15px;
    right: 20px;
    font-size: 28px;
    cursor: pointer;
    color: #6b7280;
}

.close:hover {
    color: #000;
}

.score-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin: 20px 0;
}

.score-item {
    text-align: center;
}

.score-circle {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: linear-gradient(135deg, #3b82f6, #10b981);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    font-weight: bold;
    margin: 10px auto;
}

.skills-section {
    margin: 20px 0;
}

.skill-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
}

.skill-tag {
    padding: 6px 12px;
    border-radius: 16px;
    font-size: 13px;
}

.skill-tag.matched {
    background-color: #d1fae5;
    color: #065f46;
}

.skill-tag.missing {
    background-color: #fee2e2;
    color: #991b1b;
}

.fit-section {
    margin: 20px 0;
    padding: 15px;
    background-color: #f9fafb;
    border-radius: 8px;
}

/* Loader */
#loader {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
}

.loader-content {
    text-align: center;
    color: white;
}

.spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3b82f6;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
```

3. **Test the UI:**

```bash
# Start server
python -m uvicorn api.main:app --reload

# Open browser
http://localhost:8000/dashboard

# Click "Analyze Match" on a job
# Click "Generate Resume" on a job
# Verify match scores and custom resume download
```

**Expected Result:**
- Job cards show match scores with color-coded badges
- "Analyze Match" button shows detailed modal with scores
- "Generate Resume" button creates and downloads custom resume
- UI is responsive and professional

---

## ✅ Phase 1 Complete!

**What You've Built:**
- ✅ Multi-provider AI client (Mistral + Gemini)
- ✅ Semantic job matching with embeddings
- ✅ Skill gap analysis
- ✅ Custom resume generation per job
- ✅ "Why you're a good fit" AI explanations
- ✅ Enhanced dashboard with match scores
- ✅ Database schema for matches and resumes

**Next Steps:**
Continue to Phase 2 for vision-guided scraping, or test Phase 1 thoroughly first.

---


## Phase 2: Vision-Guided Adaptive Scraping

### Overview
Replace hardcoded selectors with vision-guided navigation using Mistral Pixtral. This makes scraping adaptive and self-healing.

**Time Estimate:** 2-3 weeks
**Difficulty:** High
**Value:** ⭐⭐⭐⭐ (Reduces maintenance significantly)

---

### Step 2.1: Set Up Vision Client

**Time:** 1 hour

**File:** `ai/vision_client.py`

**Instructions:**

1. **Create vision client:**

```python
"""
Vision client for screenshot analysis and action decisions
"""

from mistralai import Mistral
import google.generativeai as genai
import base64
import os
from typing import Dict, Optional
from PIL import Image
import io

class VisionClient:
    def __init__(self):
        # Mistral for vision
        self.mistral_key = os.getenv("MISTRAL_API_KEY")
        self.mistral_client = Mistral(api_key=self.mistral_key) if self.mistral_key else None
        
        # Gemini as fallback
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
    
    def analyze_screenshot(
        self,
        screenshot_path: str,
        task: str,
        context: Optional[str] = None
    ) -> Dict:
        """
        Analyze screenshot and decide next action
        
        Args:
            screenshot_path: Path to screenshot image
            task: What we're trying to accomplish
            context: Additional context about current state
        
        Returns:
            {
                'thought': 'What the AI sees and thinks',
                'action': 'click' | 'type' | 'scroll' | 'extract' | 'done',
                'target': coordinates or text,
                'confidence': 0-100
            }
        """
        # Convert image to base64
        image_b64 = self._image_to_base64(screenshot_path)
        
        # Create prompt
        prompt = self._create_analysis_prompt(task, context)
        
        # Try Mistral Pixtral first
        try:
            response = self._analyze_with_mistral(image_b64, prompt)
            return self._parse_response(response)
        except Exception as e:
            print(f"Mistral vision error: {e}, trying Gemini")
        
        # Fallback to Gemini
        try:
            response = self._analyze_with_gemini(screenshot_path, prompt)
            return self._parse_response(response)
        except Exception as e:
            print(f"Gemini vision error: {e}")
            raise Exception("All vision providers failed")
    
    def _image_to_base64(self, image_path: str) -> str:
        """Convert image to base64 string"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    
    def _create_analysis_prompt(self, task: str, context: Optional[str]) -> str:
        """Create structured prompt for vision analysis"""
        prompt = f"""
You are a browser automation agent. Analyze this screenshot and decide the next action.

TASK: {task}

{f"CONTEXT: {context}" if context else ""}

Respond in this EXACT format:
Thought: [What you see and your reasoning]
Action: [click|type|scroll|extract|done]
Target: [coordinates as (x,y) OR text to type OR 'down'/'up' for scroll]
Confidence: [0-100]

Examples:
- To click search button: Action: click, Target: (500, 200)
- To type text: Action: type, Target: "Python developer"
- To scroll down: Action: scroll, Target: down
- To extract jobs: Action: extract, Target: job_cards
- When task complete: Action: done, Target: success

Your response:
"""
        return prompt
    
    def _analyze_with_mistral(self, image_b64: str, prompt: str) -> str:
        """Analyze with Mistral Pixtral"""
        response = self.mistral_client.chat.complete(
            model="pixtral-12b-2409",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": f"data:image/png;base64,{image_b64}"
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    
    def _analyze_with_gemini(self, image_path: str, prompt: str) -> str:
        """Analyze with Gemini Vision"""
        model = genai.GenerativeModel('gemini-2.5-flash')
        image = Image.open(image_path)
        response = model.generate_content([prompt, image])
        return response.text
    
    def _parse_response(self, response: str) -> Dict:
        """Parse AI response into structured format"""
        lines = response.strip().split('\n')
        result = {
            'thought': '',
            'action': 'done',
            'target': None,
            'confidence': 50
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith('Thought:'):
                result['thought'] = line.replace('Thought:', '').strip()
            elif line.startswith('Action:'):
                result['action'] = line.replace('Action:', '').strip().lower()
            elif line.startswith('Target:'):
                target_str = line.replace('Target:', '').strip()
                # Parse coordinates if present
                if '(' in target_str and ')' in target_str:
                    coords = target_str.strip('()').split(',')
                    result['target'] = (int(coords[0]), int(coords[1]))
                else:
                    result['target'] = target_str
            elif line.startswith('Confidence:'):
                try:
                    result['confidence'] = int(line.replace('Confidence:', '').strip())
                except:
                    result['confidence'] = 50
        
        return result

# Global instance
vision_client = VisionClient()
```

2. **Test vision client:**

```python
# test_vision.py
from ai.vision_client import vision_client
import pyautogui

# Take a screenshot
screenshot_path = "test_screenshot.png"
pyautogui.screenshot(screenshot_path)

# Analyze it
result = vision_client.analyze_screenshot(
    screenshot_path=screenshot_path,
    task="Find the search button on this page",
    context="We're on a job portal homepage"
)

print(f"Thought: {result['thought']}")
print(f"Action: {result['action']}")
print(f"Target: {result['target']}")
print(f"Confidence: {result['confidence']}%")
```

**Expected Output:**
```
Thought: I see a search input field and a blue search button at coordinates (650, 300)
Action: click
Target: (650, 300)
Confidence: 85%
```

---

