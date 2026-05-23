"""Company intelligence agent - analyzes companies for insights and hiring signals."""
import json
import re
from typing import Dict, Any, List
import httpx
from bs4 import BeautifulSoup
from ai.ai_client import get_ai_client
from ai.prompts import COMPANY_INTEL_PROMPT, PAIN_SIGNAL_PROMPT, INTENT_SCORER_PROMPT


HIRING_SIGNALS = [
    "hiring", "we're growing", "join our team", "expanding",
    "new office", "funding", "series", "acquisition",
    "rapidly growing", "scaling", "looking for talent",
    "multiple openings", "urgent hiring", "immediate start",
]

TECH_STACK_KEYWORDS = {
    "Python": ["python", "django", "flask", "fastapi"],
    "JavaScript": ["javascript", "typescript", "node.js", "react", "angular", "vue"],
    "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda"],
    "Docker": ["docker", "kubernetes", "k8s", "container"],
    "SQL": ["sql", "postgresql", "mysql", "mongodb", "database"],
    "Java": ["java", "spring", "spring boot"],
    "Go": ["golang", "go"],
    "Rust": ["rust"],
    "ML/AI": ["machine learning", "ai", "tensorflow", "pytorch", "llm"],
}


class CompanyIntelAgent:
    """Analyzes companies to generate B2B intelligence and lead scoring."""

    def __init__(self):
        self.ai = get_ai_client()
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    async def analyze_company(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Run full company analysis: intel + pain signals + intent scoring."""
        name = company.get("company_name") or company.get("name", "")
        website = company.get("website", "")
        raw_text = company.get("raw_data", {}).get("snippet", "")

        if website and not raw_text:
            raw_text = await self._fetch_website_text(website)

        company_text = f"Company: {name}\nWebsite: {website}\nAbout: {raw_text[:3000]}"

        intel_task = self._call_ai(COMPANY_INTEL_PROMPT, company_text)
        pain_task = self._call_ai(PAIN_SIGNAL_PROMPT, company_text)
        intel_raw, pain_raw = await intel_task, pain_task

        intel = self._safe_json(intel_raw, default={
            "company_size": "", "industry": "", "tech_stack": [],
            "culture_summary": "", "hiring_trend": "", "growth_indicators": [], "overall_summary": "",
        })
        pain = self._safe_json(pain_raw, default={
            "pain_signals": [], "pain_score": 0, "pain_reasoning": "",
            "automation_ideas": [], "tech_stack": [], "company_size": "", "niche": "",
        })

        result = {
            "name": name,
            "website": website,
            "size": intel.get("company_size") or pain.get("company_size", ""),
            "industry": intel.get("industry", ""),
            "tech_stack": list(set(intel.get("tech_stack", []) + pain.get("tech_stack", []))),
            "culture": intel.get("culture_summary", ""),
            "hiring_trend": intel.get("hiring_trend", ""),
            "growth_indicators": intel.get("growth_indicators", []),
            "ai_summary": intel.get("overall_summary", ""),
            "pain_signals": pain.get("pain_signals", []),
            "pain_score": pain.get("pain_score", 0),
            "pain_reasoning": pain.get("pain_reasoning", ""),
            "automation_ideas": pain.get("automation_ideas", []),
            "niche": pain.get("niche", ""),
        }

        intent_raw = await self._call_ai(INTENT_SCORER_PROMPT, json.dumps(result))
        intent = self._safe_json(intent_raw, default={"intent_score": 0.0, "priority": "cold", "reasoning": ""})
        result["intent_score"] = intent.get("intent_score", 0.0)
        result["priority"] = intent.get("priority", "cold")
        result["intent_reasoning"] = intent.get("reasoning", "")

        hiring_signals = await self._detect_hiring_signals(raw_text)
        result["hiring_signals"] = hiring_signals
        result["is_actively_hiring"] = len(hiring_signals) > 0

        detected_tech = self._detect_tech_stack(raw_text)
        if detected_tech:
            existing = set(result["tech_stack"])
            result["tech_stack"] = list(existing.union(detected_tech))

        return result

    async def _call_ai(self, system_prompt: str, user_content: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        return await self.ai.chat_completion(messages=messages, temperature=0.2, json_mode=True)

    def _safe_json(self, text: str, default: Dict) -> Dict:
        try:
            return json.loads(text)
        except Exception:
            return default

    async def _fetch_website_text(self, url: str) -> str:
        try:
            if not url.startswith("http"):
                url = f"https://{url}"
            async with httpx.AsyncClient(headers=self.headers, timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(url)
                soup = BeautifulSoup(resp.text, "lxml")
                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()
                return soup.get_text(separator="\n", strip=True)[:5000]
        except Exception:
            return ""

    async def _detect_hiring_signals(self, text: str) -> List[Dict[str, Any]]:
        """Detect hiring signals from company text."""
        signals = []
        if not text:
            return signals
        
        lower_text = text.lower()
        for signal in HIRING_SIGNALS:
            if signal in lower_text:
                context_start = max(0, lower_text.index(signal) - 50)
                context_end = min(len(text), lower_text.index(signal) + len(signal) + 50)
                signals.append({
                    "signal": signal,
                    "context": text[context_start:context_end].strip(),
                })
        
        job_count = len(re.findall(r'\b(openings?|positions?|vacancies?|roles?)\b', lower_text))
        if job_count > 0:
            signals.append({
                "signal": f"job_posting_mentions",
                "context": f"Mentioned {job_count} opening(s)/position(s)",
            })
        
        return signals

    def _detect_tech_stack(self, text: str) -> set:
        """Detect technology stack from text using keyword matching."""
        if not text:
            return set()
        
        detected = set()
        lower_text = text.lower()
        
        for tech, keywords in TECH_STACK_KEYWORDS.items():
            for kw in keywords:
                if kw in lower_text:
                    detected.add(tech)
                    break
        
        return detected

    async def analyze_job_company(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the company associated with a job posting."""
        company_name = job_data.get("company", "")
        description = job_data.get("description", "")
        
        if not company_name:
            return {"error": "No company name provided"}
        
        company_info = {
            "company_name": company_name,
            "raw_data": {"snippet": description},
        }
        
        return await self.analyze_company(company_info)
