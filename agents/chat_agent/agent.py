"""Chat Agent - Routes user messages to appropriate tools."""
import os
import sys
import json
import re
import asyncio
import subprocess
import httpx
from typing import List, Dict, Any, Optional
from ai.ai_client import get_ai_client


class SkillsShClient:
    """Client for skills.sh tools."""

    def __init__(self):
        self.base = "https://skills.sh"

    async def analyze_resume_skills(self, resume_text: str, job_description: str = "") -> Dict:
        """Analyze resume skills using skills.sh."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.base}/api/run",
                    json={
                        "skill": "paramchoudhary/resumeskills/job-description-analyzer",
                        "input": {
                            "resume": resume_text[:3000],
                            "job_description": job_description[:2000] if job_description else ""
                        }
                    }
                )
                if resp.status_code == 200:
                    return resp.json()
        except:
            pass
        return {}

    async def search_skills(self, query: str) -> Dict:
        """Search for trending skills/jobs."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base}/api/run",
                    params={
                        "skill": "aradotso/trending-skills/karpathy-jobs-bls-visualizer",
                        "query": query
                    }
                )
                if resp.status_code == 200:
                    return resp.json()
        except:
            pass
        return {}


class ChatAgent:
    """Routes user messages to tools: browser, scraper, search, resume analyzer."""

    def __init__(self):
        self.ai = get_ai_client()
        self.skills = SkillsShClient()
        self._tool_log = []

    def _log_tool(self, name: str, status: str = "running", result: str = ""):
        self._tool_log.append({"name": name, "status": status, "result": result})

    def get_tool_log(self) -> List[Dict]:
        log = self._tool_log.copy()
        self._tool_log = []
        return log

    async def route_message(self, message: str, context: Dict) -> Dict:
        """Decide which tool/action to use based on user message."""
        msg_lower = message.lower()

        # Determine intent
        intent = await self._classify_intent(message, context)
        context["intent"] = intent

        self._tool_log = []

        # Execute based on intent
        if intent == "search_jobs":
            return await self._handle_search_jobs(message, context)
        elif intent == "browse_website":
            return await self._handle_browse_website(message, context)
        elif intent == "analyze_resume":
            return await self._handle_analyze_resume(message, context)
        elif intent == "crawl_companies":
            return await self._handle_crawl_companies(message, context)
        elif intent == "apply_jobs":
            return await self._handle_apply_jobs(message, context)
        elif intent == "skills_search":
            return await self._handle_skills_search(message, context)
        elif intent == "general":
            return await self._handle_general(message, context)
        else:
            return await self._handle_general(message, context)

    async def _classify_intent(self, message: str, context: Dict) -> str:
        """Classify user message intent."""
        msg_lower = message.lower()

        # Priority 1: Job search (highest priority)
        search_triggers = ["job", "position", "opening", "vacancy", "role", "career", "work"]
        action_triggers = ["find", "search", "get", "need", "want", "show", "look", "fetch", "give", "list", "recommend", "suggest", "based on"]
        
        if any(w in msg_lower for w in search_triggers):
            if any(w in msg_lower for w in action_triggers):
                return "search_jobs"
            # If user mentions resume and keywords are set, assume search
            if "resume" in msg_lower and context.get("keywords"):
                return "search_jobs"

        # Priority 2: Browse specific website
        if any(w in msg_lower for w in ["browse", "visit", "open", "go to", "navigate"]):
            return "browse_website"

        # Priority 3: Crawl companies
        if any(w in msg_lower for w in ["company career", "career page", "company website"]):
            return "crawl_companies"

        # Priority 4: Resume analysis (only if explicitly about analyzing)
        if any(w in msg_lower for w in ["analyze my resume", "analyze my cv", "review my resume", "review my cv", "improve my resume", "improve my cv", "resume feedback", "cv feedback", "how is my resume", "rate my resume"]):
            return "analyze_resume"

        # Priority 5: Skills search
        if any(w in msg_lower for w in ["trending skills", "what skills", "market demand", "skill demand"]):
            return "skills_search"

        # Use AI for ambiguous cases
        try:
            prompt = f"""Classify this user message into ONE intent:
Message: {message}

Intents: search_jobs, browse_website, analyze_resume, crawl_companies, apply_jobs, general

Reply with ONLY the intent name."""

            response = await self.ai.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=20,
            )
            intent = response.strip().lower().replace(" ", "_")
            if intent in ["search_jobs", "browse_website", "analyze_resume", "crawl_companies", "apply_jobs", "general"]:
                return intent
        except:
            pass

        return "general"

    async def _handle_search_jobs(self, message: str, context: Dict) -> Dict:
        """Search for jobs using Dual Model Orchestration (Step 3.5 Brain + UI-TARS Hands)."""
        msg_lower = message.lower()
        resume = context.get("resume_text", "")

        # Step 1: Analyze resume if available
        profile = None
        if resume and len(resume.strip()) > 50:
            self._log_tool("resume_analysis", "starting", "Analyzing your resume...")
            try:
                from agents.resume_analyzer import ResumeAnalyzer
                analyzer = ResumeAnalyzer()
                profile = await analyzer.analyze(resume)
                self._log_tool("resume_analysis", "complete",
                    f"Found {len(profile.get('skills', []))} skills, fresher={profile.get('is_fresher')}, roles={profile.get('target_roles', [])}")
            except Exception as e:
                self._log_tool("resume_analysis", "error", str(e))

        # Step 2: Extract location from message (only if explicitly mentioned)
        location = context.get("location", "Hyderabad")
        # Only override if user explicitly mentions a city in the message
        city_pattern = r'\b(Hyderabad|Bangalore|Bengaluru|Chennai|Mumbai|Delhi|Pune|Kolkata|Noida|Gurgaon|Gurugram|Kochi|Vizag|Ahmedabad|Jaipur|Lucknow|Chandigarh|Coimbatore|Mangalore|Mysore)\b'
        city_match = re.search(city_pattern, message, re.IGNORECASE)
        if city_match:
            location = city_match.group(1).title()

        # Step 2.5: Extract keyword from message (overrides form input)
        # Only extract if message contains a clear skill/tech keyword
        # Ignore numbers like "21" (job count), "find", "search", etc.
        keyword_override = None
        # Look for known tech keywords in message
        tech_keywords = [
            'java', 'python', 'sql', 'azure', 'aws', 'react', 'angular', 'node',
            'appian', 'bpm', 'sail', 'iot', 'cybersecurity', 'data analyst',
            'machine learning', 'ml', 'ai', 'devops', 'docker', 'kubernetes',
            'spring', 'django', 'flask', 'c#', '.net', 'php', 'ruby', 'go',
            'rust', 'swift', 'kotlin', 'typescript', 'javascript', 'html', 'css',
            'sap', 'salesforce', 'tableau', 'power bi', 'excel', 'sap',
            'blockchain', 'cloud', 'network', 'security', 'testing', 'qa',
            'full stack', 'backend', 'frontend', 'mobile', 'ios', 'android',
        ]
        msg_lower = message.lower()
        for tech in tech_keywords:
            if tech in msg_lower:
                keyword_override = tech
                break
        
        # Use extracted keyword if found, else use form keywords
        if keyword_override:
            search_keywords = [keyword_override]
            self._log_tool("keyword_extraction", "message", f"Using keyword from message: {keyword_override}")
        else:
            form_keywords = context.get("keywords", "")
            if form_keywords and isinstance(form_keywords, str):
                search_keywords = [k.strip() for k in form_keywords.split(",") if k.strip()]
            elif form_keywords and isinstance(form_keywords, list):
                search_keywords = form_keywords
            else:
                search_keywords = []
            
            if not search_keywords:
                search_keywords = ["Developer"]
            self._log_tool("keyword_extraction", "form", f"Using form keywords: {', '.join(search_keywords)}")

        # Step 3: Determine experience level
        ui_experience = context.get("experience", "").strip().lower()
        user_exp_years = None
        is_fresher = True

        if ui_experience == "fresher":
            is_fresher = True
            user_exp_years = 0
        elif ui_experience == "experienced":
            is_fresher = False
            user_exp_years = None
        elif ui_experience.isdigit():
            user_exp_years = int(ui_experience)
            is_fresher = user_exp_years <= 2
        else:
            if any(w in msg_lower for w in ["fresher", "fresher job", "entry level", "no experience", "just passed", "recent graduate"]):
                is_fresher = True
                user_exp_years = 0
            elif any(w in msg_lower for w in ["experienced", "experienced job", "senior", "mid level"]):
                is_fresher = False
                user_exp_years = None
            else:
                year_match = re.search(r'(\d+)\s*\+?\s*(?:years?|yrs?|yr)\s*(?:of\s*)?(?:experience|exp)?', msg_lower)
                if year_match:
                    user_exp_years = int(year_match.group(1))
                    is_fresher = user_exp_years <= 2
                else:
                    is_fresher = profile.get("is_fresher", True) if profile else True
                    if not is_fresher:
                        user_exp_years = None

        # Build enriched context for orchestrator
        # Use portals from frontend settings, not message parsing
        frontend_portals = context.get("portals", [])
        
        orchestrator_context = {
            "user_id": context.get("user_id"),
            "resume_text": resume,
            "location": location,
            "target_count": context.get("target_count", 20),
            "profile": profile or {},
            "portals": frontend_portals if frontend_portals else None,
            "keywords": search_keywords,
            "experience": context.get("experience", "fresher"),  # Pass UI experience setting
        }

        # Execute dual-model search
        try:
            from agents.dual_model_orchestrator import DualModelOrchestrator
            orchestrator = DualModelOrchestrator()
            
            result = await orchestrator.run_search(message, orchestrator_context)
            
            # Merge tool logs
            for tool_use in result.get("tool_uses", []):
                self._log_tool(tool_use["name"], tool_use["status"], tool_use["result"])
            
            await orchestrator.cleanup()
            
            return {
                "response": result["response"],
                "tool_uses": self.get_tool_log(),
                "jobs": result.get("jobs", []),
            }
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self._log_tool("dual_model_orchestrator", "error", f"{str(e)}\n{error_detail}")
            return {
                "response": f"Error during job search: {str(e)}. Please try again.",
                "tool_uses": self.get_tool_log(),
                "jobs": [],
            }

    async def _handle_browse_website(self, message: str, context: Dict) -> Dict:
        """Browse a specific website using UI-TARS."""
        url_match = re.search(r'(https?://[^\s]+)', message)
        url = url_match.group(1) if url_match else None

        if not url:
            site_map = {
                "youtube": "https://www.youtube.com",
                "google": "https://www.google.com",
                "twitter": "https://twitter.com",
                "x.com": "https://x.com",
                "facebook": "https://www.facebook.com",
                "instagram": "https://www.instagram.com",
                "linkedin": "https://www.linkedin.com",
                "github": "https://github.com",
            }
            msg_lower = message.lower()
            for site, site_url in site_map.items():
                if site in msg_lower:
                    url = site_url
                    break

        if not url:
            return {"response": f"I couldn't find a website to browse in your message. Try saying 'open youtube.com' or provide a URL.", "tool_uses": self.get_tool_log(), "jobs": []}

        self._log_tool("ui_tars_browse", "starting", f"Browsing {url} with UI-TARS")

        try:
            from agents.vision_scraper.ui_tars_agent import UITarsAgent
            from agents.browser_agent.browser_controller import BrowserController
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            mistral_api_key = os.getenv("MISTRAL_API_KEY")
            if not mistral_api_key:
                raise Exception("MISTRAL_API_KEY not configured")
            
            browser = BrowserController(headless=False)
            await browser.start()
            
            try:
                agent = UITarsAgent(browser, mistral_api_key, max_steps=15)
                
                # Extract task from message
                task = message.replace(url, "").strip()
                if not task or task.lower() in ["open", "browse", "visit", "go to", "navigate"]:
                    task = f"Open {url} and explore the main content. Summarize what you see."
                else:
                    task = f"{task} on {url}"
                
                result = await agent.run(task, start_url=url)
                
                if result.get("status") == "success":
                    self._log_tool("ui_tars_browse", "complete", f"Successfully browsed {url}")
                    response = f"I completed the task on {url} using UI-TARS.\n\n"
                    response += f"**Actions taken:** {result.get('steps', 0)} steps\n"
                    response += f"**Status:** {result.get('status')}\n\n"
                    response += "The browser has been closed. Check the dashboard for any results."
                else:
                    self._log_tool("ui_tars_browse", "error", result.get("error", "Unknown error"))
                    response = f"UI-TARS browsing failed: {result.get('error', 'Unknown error')}."
                
                return {"response": response, "tool_uses": self.get_tool_log(), "jobs": []}
            finally:
                await browser.close()
                
        except Exception as e:
            self._log_tool("ui_tars_browse", "error", str(e))
            return {"response": f"Error browsing {url}: {e}", "tool_uses": self.get_tool_log(), "jobs": []}

    async def _handle_analyze_resume(self, message: str, context: Dict) -> Dict:
        """Analyze user's resume."""
        resume = context.get("resume_text", "")

        if not resume:
            return {
                "response": "Please upload your resume or paste it in the sidebar first.",
                "tool_uses": self.get_tool_log(),
                "jobs": []
            }

        self._log_tool("resume_analyzer", "starting", "Analyzing resume with AI + skills.sh...")

        # Try skills.sh first
        skills_result = await self.skills.analyze_resume_skills(resume)
        skills_info = ""
        if skills_result:
            skills_info = f"\n\nSkills.sh Analysis:\n{json.dumps(skills_result, indent=2)[:1000]}"
            self._log_tool("skills.sh", "complete", "Resume skills analyzed")

        prompt = f"""You are an expert resume reviewer. Analyze this resume:

{resume[:3000]}

{skills_info}

Provide:
1. Overall assessment (strengths/weaknesses)
2. Key skills identified
3. Suggested improvements
4. Job roles this person is suited for
5. Match against: {context.get('keywords', 'general tech roles')}

Be specific and actionable."""

        try:
            response = await self.ai.chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert resume reviewer."},
                    {"role": "user", "content": prompt}
                ],
                model="mistralai/mistral-large-3-675b-instruct-2512",
                temperature=0.3,
                max_tokens=2000,
            )

            self._log_tool("resume_analyzer", "complete", "Analysis done")

            return {"response": response, "tool_uses": self.get_tool_log(), "jobs": []}
        except Exception as e:
            return {"response": f"Error analyzing resume: {e}", "tool_uses": self.get_tool_log(), "jobs": []}

    async def _handle_crawl_companies(self, message: str, context: Dict) -> Dict:
        """Crawl company career pages."""
        keywords = context.get("keywords", "tech")
        location = context.get("location", "Hyderabad")

        self._log_tool("company_crawler", "starting", f"Searching for {keywords} companies")

        # Use AI to identify companies to check
        try:
            company_prompt = f"""Based on this message, list 5 company names or career page URLs to check for job openings.
Message: {message}
Keywords: {keywords}
Location: {location}

Reply with a JSON array of URLs or company names: ["url1", "url2", ...]"""

            response = await self.ai.chat_completion(
                messages=[{"role": "user", "content": company_prompt}],
                model="mistralai/mistral-large-3-675b-instruct-2512",
                temperature=0.1,
                max_tokens=500,
            )

            json_match = re.search(r'\[[\s\S]*\]', response)
            companies = json.loads(json_match.group()) if json_match else []
        except:
            companies = []

        if not companies:
            companies = [
                f"https://www.google.com/search?q={keywords}+jobs+{location}",
            ]

        jobs = []
        from agents.browser_agent.agent import BrowserAgent
        agent = BrowserAgent(headless=False)
        await agent.browser.start()

        try:
            for company in companies[:3]:
                url = company if company.startswith("http") else f"https://{company}/careers"
                self._log_tool("crawl", "visiting", url)

                await agent.browser.go_to(url)
                await agent.browser.wait(2)
                page_jobs = await agent.browser.extract_jobs()

                for job in page_jobs:
                    if not any(j.get("source_url") == job.get("source_url") for j in jobs):
                        job["source"] = "company"
                        jobs.append(job)

                self._log_tool("crawl", "found", f"{len(page_jobs)} jobs at {company}")

            self._log_tool("company_crawler", "complete", f"Found {len(jobs)} total jobs")
        finally:
            await agent.browser.close()

        if not jobs:
            return {
                "response": f"I checked several company career pages but couldn't find job listings. The pages may require interaction or have dynamic content.",
                "tool_uses": self.get_tool_log(),
                "jobs": []
            }

        response = f"Found {len(jobs)} jobs from company career pages:\n\n"
        for i, job in enumerate(jobs[:10], 1):
            response += f"{i}. {job['title']} at {job['company']} - {job['location']}\n"

        return {"response": response, "tool_uses": self.get_tool_log(), "jobs": jobs}

    async def _handle_skills_search(self, message: str, context: Dict) -> Dict:
        """Search for trending skills."""
        keywords = context.get("keywords", "Python")
        self._log_tool("skills_search", "starting", f"Searching trending skills for {keywords}")

        result = await self.skills.search_skills(keywords)

        if result:
            self._log_tool("skills.sh", "complete", "Trending skills found")
            response = f"Trending skills and market data for '{keywords}':\n\n"
            response += json.dumps(result, indent=2)[:2000]
        else:
            # Fallback to AI
            self._log_tool("skills_search", "fallback", "Using AI analysis")
            prompt = f"""What are the trending skills and market demand for: {keywords}
Location: {context.get('location', 'India')}
Provide current market insights, salary ranges, and in-demand skills."""

            response = await self.ai.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="mistralai/mistral-large-3-675b-instruct-2512",
                temperature=0.3,
                max_tokens=1500,
            )

        return {"response": response, "tool_uses": self.get_tool_log(), "jobs": []}

    async def _handle_apply_jobs(self, message: str, context: Dict) -> Dict:
        """Apply to jobs using UI-TARS autonomous agent."""
        import asyncio
        jobs = context.get("jobs", [])
        if not jobs:
            return {
                "response": "No jobs to apply to. Search for jobs first.",
                "tool_uses": self.get_tool_log(),
                "jobs": []
            }

        resume = context.get("resume_text", "")
        applied = []
        failed = []

        self._log_tool("ui_tars_apply", "starting", f"Applying to {len(jobs[:3])} jobs using UI-TARS...")

        try:
            from agents.vision_scraper.ui_tars_agent import UITarsAgent
            from agents.browser_agent.browser_controller import BrowserController
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            mistral_api_key = os.getenv("MISTRAL_API_KEY")
            if not mistral_api_key:
                raise Exception("MISTRAL_API_KEY not configured")
            
            browser = BrowserController(headless=False)
            await browser.start()
            
            try:
                agent = UITarsAgent(browser, mistral_api_key, max_steps=50)
                
                # Apply to first 3 jobs
                for job in jobs[:3]:
                    apply_url = job.get("apply_url", "")
                    if not apply_url:
                        failed.append({"job": job, "reason": "No apply URL"})
                        continue
                    
                    self._log_tool("ui_tars_apply", "applying", f"Applying to {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                    
                    task = f"Apply to this job: {job.get('title', 'N/A')} at {job.get('company', 'N/A')}. Fill out the application form with the following resume information:\n\n{resume[:1000]}\n\nComplete all required fields and submit the application."
                    
                    result = await agent.run(task, start_url=apply_url)
                    
                    if result.get("status") == "success":
                        applied.append(job)
                        self._log_tool("ui_tars_apply", "success", f"Applied to {job.get('title', 'N/A')}")
                    else:
                        failed.append({"job": job, "reason": result.get("error", "Unknown error")})
                        self._log_tool("ui_tars_apply", "error", f"Failed to apply to {job.get('title', 'N/A')}: {result.get('error')}")
                
                # Format response
                response = f"UI-TARS auto-apply completed:\n\n"
                response += f"**Successfully Applied:** {len(applied)} jobs\n"
                for job in applied:
                    response += f"✓ {job.get('title', 'N/A')} at {job.get('company', 'N/A')}\n"
                
                if failed:
                    response += f"\n**Failed:** {len(failed)} jobs\n"
                    for item in failed:
                        job = item["job"]
                        reason = item["reason"]
                        response += f"✗ {job.get('title', 'N/A')} at {job.get('company', 'N/A')} - {reason}\n"
                
                response += "\nYou can view application status in your dashboard."
                
                return {
                    "response": response,
                    "tool_uses": self.get_tool_log(),
                    "jobs": jobs
                }
            finally:
                await browser.close()
                
        except Exception as e:
            self._log_tool("ui_tars_apply", "error", str(e))
            return {
                "response": f"Error during UI-TARS auto-apply: {e}. Please try again.",
                "tool_uses": self.get_tool_log(),
                "jobs": []
            }

    async def _handle_general(self, message: str, context: Dict) -> Dict:
        """General conversation."""
        msg_lower = message.lower()

        # Handle common general requests without AI
        if any(w in msg_lower for w in ["hello", "hi ", "hey", "good morning", "good evening"]):
            return {"response": "Hello! I'm your AI Job Application Agent. I can help you:\n\n• **Search jobs** - 'Find Python jobs in Bangalore'\n• **Browse websites** - 'Open youtube.com'\n• **Analyze resume** - Upload your resume and ask for feedback\n• **Apply to jobs** - Auto-fill application forms\n\nWhat would you like to do?", "tool_uses": self.get_tool_log(), "jobs": []}

        if any(w in msg_lower for w in ["thank", "thanks"]):
            return {"response": "You're welcome! Let me know if you need help with job searching or anything else.", "tool_uses": self.get_tool_log(), "jobs": []}

        if any(w in msg_lower for w in ["help", "what can you do", "capabilities"]):
            return {"response": "I can help you with:\n\n1. **Job Search** - Search across Naukri, Indeed, LinkedIn, and more\n2. **Resume Analysis** - Get feedback on your resume\n3. **Website Browsing** - Open and extract content from websites\n4. **Job Applications** - Auto-fill and submit applications\n5. **Company Research** - Crawl company career pages\n\nJust ask me anything related to your job search!", "tool_uses": self.get_tool_log(), "jobs": []}

        # Try AI for other general requests
        resume_snippet = context.get("resume_text", "Not provided")[:500]

        prompt = f"""You are a job search assistant AI. Be concise and helpful.

User message: {message}

If the user is asking about something unrelated to jobs, be friendly but steer them toward job search help."""

        try:
            response = await self.ai.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a helpful job search assistant."},
                    {"role": "user", "content": prompt}
                ],
                model="mistralai/mistral-large-3-675b-instruct-2512",
                temperature=0.7,
                max_tokens=1000,
            )
            return {"response": response, "tool_uses": self.get_tool_log(), "jobs": []}
        except Exception as e:
            return {"response": f"I'm currently having trouble connecting to my AI brain. I can still help with:\n\n• **Job search** - Just tell me what jobs to find\n• **Browse websites** - Say 'open [website]'\n• **Resume upload** - Upload your resume in the sidebar\n\nError: {e}", "tool_uses": self.get_tool_log(), "jobs": []}
