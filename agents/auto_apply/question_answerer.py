"""Screening question answerer - AI-based answers from resume data."""
import logging
from typing import Dict, Any, List, Optional

from agents.vision_scraper.multi_provider_client import MultiProviderAIClient

logger = logging.getLogger(__name__)


class ScreeningQuestionAnswerer:
    """Generates answers for job application screening questions."""

    def __init__(self, ai_client: Optional[MultiProviderAIClient] = None):
        self.ai_client = ai_client

    async def answer_question(
        self,
        question: str,
        question_type: str,
        options: List[str],
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate answer for a screening question."""
        if question_type == "yes_no":
            return self._answer_yes_no(question, resume_data, job_data)
        elif question_type == "multiple_choice":
            return await self._answer_multiple_choice(question, options, resume_data, job_data)
        elif question_type == "number":
            return self._answer_number(question, resume_data)
        else:
            return await self._answer_text(question, resume_data, job_data)

    def _answer_yes_no(
        self,
        question: str,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Answer yes/no questions based on resume data."""
        lower_q = question.lower()
        
        if any(kw in lower_q for kw in ["authorized", "work authorization", "citizen", "legal"]):
            return {"answer": "Yes", "confidence": 0.9, "needs_review": False}
        
        if any(kw in lower_q for kw in ["sponsor", "sponsorship", "visa"]):
            return {"answer": "No", "confidence": 0.7, "needs_review": True, "flag": "Visa sponsorship question"}
        
        if any(kw in lower_q for kw in ["relocate", "relocation"]):
            return {"answer": "Yes", "confidence": 0.6, "needs_review": True, "flag": "Relocation preference"}
        
        if any(kw in lower_q for kw in ["remote"]):
            return {"answer": "Yes", "confidence": 0.8, "needs_review": False}
        
        if any(kw in lower_q for kw in ["background", "criminal"]):
            return {"answer": "No", "confidence": 0.8, "needs_review": False}
        
        if any(kw in lower_q for kw in ["equal opportunity", "veteran", "disability", "demographic"]):
            return {"answer": "Prefer not to say", "confidence": 0.9, "needs_review": False}
        
        if any(kw in lower_q for kw in ["experience", "years"]):
            years = resume_data.get("experience_years", 0)
            return {"answer": "Yes" if years > 0 else "No", "confidence": 0.8, "needs_review": False}
        
        return {"answer": "Yes", "confidence": 0.5, "needs_review": True, "flag": "Unclear yes/no question"}

    async def _answer_multiple_choice(
        self,
        question: str,
        options: List[str],
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Answer multiple choice questions."""
        if not options:
            return {"answer": "", "confidence": 0.3, "needs_review": True, "flag": "No options provided"}
        
        lower_q = question.lower()
        
        if any(kw in lower_q for kw in ["education", "degree", "highest"]):
            education = resume_data.get("education", "").lower()
            for opt in options:
                lower_opt = opt.lower()
                if "bachelor" in lower_opt and ("bachelor" in education or "bs" in education or "ba" in education):
                    return {"answer": opt, "confidence": 0.9, "needs_review": False}
                if "master" in lower_opt and ("master" in education or "ms" in education or "ma" in education or "mba" in education):
                    return {"answer": opt, "confidence": 0.9, "needs_review": False}
                if "phd" in lower_opt and "phd" in education:
                    return {"answer": opt, "confidence": 0.9, "needs_review": False}
            return {"answer": options[0], "confidence": 0.4, "needs_review": True, "flag": "Education match uncertain"}
        
        if any(kw in lower_q for kw in ["experience", "years"]):
            years = resume_data.get("experience_years", 0)
            for opt in options:
                if str(int(years)) in opt or f"{int(years)}-" in opt:
                    return {"answer": opt, "confidence": 0.9, "needs_review": False}
            return {"answer": options[-1] if years > 5 else options[0], "confidence": 0.5, "needs_review": True, "flag": "Experience range uncertain"}
        
        if any(kw in lower_q for kw in ["salary", "compensation", "expected"]):
            return {"answer": "Negotiable", "confidence": 0.5, "needs_review": True, "flag": "Salary expectation needs user input"}
        
        if any(kw in lower_q for kw in ["notice period", "start date", "available"]):
            return {"answer": options[0] if options else "Immediate", "confidence": 0.6, "needs_review": True, "flag": "Notice period needs user input"}
        
        return {"answer": options[0], "confidence": 0.3, "needs_review": True, "flag": "Unclear multiple choice question"}

    def _answer_number(
        self,
        question: str,
        resume_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Answer numeric questions."""
        lower_q = question.lower()
        
        if any(kw in lower_q for kw in ["year", "experience"]):
            years = resume_data.get("experience_years", 0)
            return {"answer": str(int(years)), "confidence": 0.9, "needs_review": False}
        
        if any(kw in lower_q for kw in ["salary", "compensation", "ctc"]):
            return {"answer": "", "confidence": 0.3, "needs_review": True, "flag": "Salary needs user input"}
        
        if any(kw in lower_q for kw in ["notice", "days"]):
            return {"answer": "30", "confidence": 0.5, "needs_review": True, "flag": "Notice period needs user input"}
        
        if any(kw in lower_q for kw in ["age"]):
            return {"answer": "", "confidence": 0.3, "needs_review": True, "flag": "Age question - skip or user input"}
        
        return {"answer": "0", "confidence": 0.3, "needs_review": True, "flag": "Unclear numeric question"}

    async def _answer_text(
        self,
        question: str,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate text answer using AI."""
        if not self.ai_client:
            return self._fallback_text_answer(question, resume_data)
        
        prompt = f"""
Answer this job application screening question based on the candidate's resume.
Be concise and honest. Return ONLY the answer text.

QUESTION: {question}

CANDIDATE BACKGROUND:
- Experience: {resume_data.get('experience_years', 0)} years
- Skills: {', '.join(resume_data.get('skills', [])[:10])}
- Current Role: {resume_data.get('current_role', 'Professional')}
- Summary: {resume_data.get('experience', '')[:500]}

TARGET JOB: {job_data.get('title', '')} at {job_data.get('company', '')}

ANSWER:
"""
        try:
            response = self.ai_client.vision_complete(
                image=b"",
                prompt=prompt,
            )
            answer = response.get("text", "").strip()
            if answer:
                return {"answer": answer, "confidence": 0.7, "needs_review": True, "flag": "AI-generated text answer"}
        except Exception as e:
            logger.warning(f"AI text answer failed: {e}")
        
        return self._fallback_text_answer(question, resume_data)

    def _fallback_text_answer(
        self,
        question: str,
        resume_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate text answer without AI."""
        lower_q = question.lower()
        
        if any(kw in lower_q for kw in ["cover letter", "why interested", "why apply"]):
            return {
                "answer": f"I am interested in this position because it aligns with my {resume_data.get('experience_years', 0)} years of experience in {', '.join(resume_data.get('skills', [])[:3])}. I am excited about the opportunity to contribute and grow.",
                "confidence": 0.5,
                "needs_review": True,
                "flag": "Generic cover letter - needs personalization",
            }
        
        if any(kw in lower_q for kw in ["summary", "about yourself", "introduce"]):
            return {
                "answer": f"Professional with {resume_data.get('experience_years', 0)} years of experience. Key skills: {', '.join(resume_data.get('skills', [])[:5])}.",
                "confidence": 0.6,
                "needs_review": True,
                "flag": "Summary needs personalization",
            }
        
        return {
            "answer": "",
            "confidence": 0.3,
            "needs_review": True,
            "flag": "No suitable answer - user input required",
        }
