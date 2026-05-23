"""
Semantic job matching using embeddings and AI analysis
Calculates match scores, identifies skill gaps, generates fit explanations
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Dict, List, Tuple
import re
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai.multi_provider_client import ai_client


class JobMatcher:
    def __init__(self):
        # Load embedding model (runs locally, free)
        print("Loading sentence transformer model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded successfully!")
    
    def calculate_match_score(
        self,
        resume_data: Dict,
        job_data: Dict
    ) -> Dict:
        """
        Calculate comprehensive match score between resume and job
        
        Args:
            resume_data: Dict with 'skills', 'experience_years', 'education', etc.
            job_data: Dict with 'title', 'description', 'requirements', etc.
        
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
            skills = resume_data['skills']
            if isinstance(skills, list):
                parts.append(f"Skills: {', '.join(skills)}")
            else:
                parts.append(f"Skills: {skills}")
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
        resume_skills = set()
        skills = resume_data.get('skills', [])
        if isinstance(skills, list):
            resume_skills = set(s.lower() for s in skills)
        elif isinstance(skills, str):
            resume_skills = set(s.strip().lower() for s in skills.split(','))
        
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
        """Extract skills from job description using AI"""
        prompt = f"""
Extract technical skills from this job description.
Return ONLY a comma-separated list of skills, nothing else.

Job: {job_data.get('title', '')}
Description: {job_data.get('description', '')[:500]}

Skills:
"""
        
        try:
            response = ai_client.chat_complete(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            skills = [s.strip().lower() for s in response.split(',') if s.strip()]
            return set(skills)
        except Exception as e:
            print(f"Error extracting skills: {e}")
            return set()
    
    def _extract_required_experience(self, job_data: Dict) -> int:
        """Extract required years of experience"""
        description = job_data.get('description', '').lower()
        
        # Look for patterns like "3+ years", "5 years experience"
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
        resume_skills = set()
        skills = resume_data.get('skills', [])
        if isinstance(skills, list):
            resume_skills = set(s.lower() for s in skills)
        elif isinstance(skills, str):
            resume_skills = set(s.strip().lower() for s in skills.split(','))
        
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
        skills = resume_data.get('skills', [])
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(',')]
        
        prompt = f"""
Write a concise 2-3 sentence explanation of why this candidate is a good fit for this job.
Focus on strengths and matched skills. Be encouraging but honest.

Job: {job_data.get('title', '')}
Company: {job_data.get('company', '')}

Candidate Skills: {', '.join(skills[:10])}
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
        except Exception as e:
            print(f"Error generating fit explanation: {e}")
            return f"You have a {score:.0f}% match with this position based on your skills and experience."


# Global instance
job_matcher = JobMatcher()
