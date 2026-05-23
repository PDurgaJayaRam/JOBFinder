"""Resume match agent - compares resumes to job descriptions."""
import json
from typing import Dict, Any
from ai.ai_client import get_ai_client
from ai.prompts import RESUME_MATCH_PROMPT


class ResumeMatchAgent:
    """Scores resume against job description using AI."""

    def __init__(self):
        self.ai = get_ai_client()

    async def compare(self, resume_text: str, job: Dict[str, Any]) -> Dict[str, Any]:
        """Return match score with weighted formula, ATS score, missing skills, and recommendations."""
        description = job.get("description", "")
        title = job.get("title", job.get("role", ""))
        required_skills = job.get("required_skills", [])
        preferred_skills = job.get("preferred_skills", [])

        messages = [
            {"role": "system", "content": RESUME_MATCH_PROMPT},
            {
                "role": "user",
                "content": f"RESUME:\n{resume_text[:3000]}\n\nJOB TITLE: {title}\nREQUIRED SKILLS: {', '.join(required_skills)}\nPREFERRED SKILLS: {', '.join(preferred_skills)}\n\nJOB DESCRIPTION:\n{description[:3000]}",
            },
        ]

        try:
            raw = await self.ai.chat_completion(messages=messages, temperature=0.2, json_mode=True)
            result = json.loads(raw)
            # Ensure all required fields exist
            if "required_match_percent" not in result:
                result["required_match_percent"] = result.get("match_score", 0)
            if "preferred_match_percent" not in result:
                result["preferred_match_percent"] = 0
            if "overall_match_score" not in result:
                result["overall_match_score"] = result.get("match_score", 0)
            if "missing_required_skills" not in result:
                result["missing_required_skills"] = result.get("missing_skills", [])
            if "missing_preferred_skills" not in result:
                result["missing_preferred_skills"] = []
            if "gap_analysis" not in result:
                result["gap_analysis"] = {"critical_gaps": [], "major_gaps": [], "minor_gaps": []}
            # For backward compatibility, also set match_score to overall_match_score
            result["match_score"] = result.get("overall_match_score", 0)
            return result
        except Exception:
            # Fallback heuristic with new fields
            resume_lower = resume_text.lower()
            desc_lower = description.lower()
            common_skills = [
                "python", "sql", "javascript", "react", "node", "aws",
                "docker", "kubernetes", "java", "c++", "go", "rust",
                "data analysis", "machine learning", "excel", "tableau",
                "powerbi", "pandas", "numpy", "scikit-learn", "tensorflow",
            ]
            matched = [s for s in common_skills if s in resume_lower and s in desc_lower]
            missing = [s for s in common_skills if s not in resume_lower and s in desc_lower]
            score = min(100, int((len(matched) / max(len(matched) + len(missing), 1)) * 100))
            return {
                "required_match_percent": score,
                "preferred_match_percent": score,
                "overall_match_score": score,
                "match_score": score,
                "ats_score": score,
                "strong_matches": matched,
                "missing_required_skills": missing,
                "missing_preferred_skills": [],
                "gap_analysis": {"critical_gaps": [], "major_gaps": [], "minor_gaps": missing},
                "recommendations": [f"Add {s} to your resume" for s in missing[:3]],
                "overall_assessment": "Heuristic fallback scoring applied.",
            }
