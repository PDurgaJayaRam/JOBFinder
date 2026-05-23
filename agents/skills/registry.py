"""AI Skills Registry - Integrated skills for the job search agent."""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class SkillCategory(Enum):
    JOB_SEARCH = "job_search"
    BROWSER_AUTOMATION = "browser_automation"
    RESUME_PARSING = "resume_parsing"
    APPLICATION = "application"
    OUTREACH = "outreach"
    ANALYTICS = "analytics"


@dataclass
class AgentSkill:
    """Represents an AI agent skill capability."""
    name: str
    description: str
    category: SkillCategory
    enabled: bool = True
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


class AISkillsRegistry:
    """Registry of all AI agent skills."""
    
    def __init__(self):
        self.skills: Dict[str, AgentSkill] = {}
        self._register_default_skills()
    
    def _register_default_skills(self):
        """Register the core skills for our job search agent."""
        
        # Browser Automation Skills
        self.register(AgentSkill(
            name="browser_navigate",
            description="Navigate to URLs and wait for page load",
            category=SkillCategory.BROWSER_AUTOMATION,
            config={"timeout": 60000, "wait_for": "networkidle"}
        ))
        
        self.register(AgentSkill(
            name="browser_scrape",
            description="Extract structured data from web pages",
            category=SkillCategory.BROWSER_AUTOMATION,
            config={"extract_text": True}
        ))
        
        self.register(AgentSkill(
            name="browser_fill_form",
            description="Fill form fields with provided data",
            category=SkillCategory.BROWSER_AUTOMATION,
            config={"fill_strategy": "smart"}
        ))
        
        # Job Search Skills
        self.register(AgentSkill(
            name="job_search_indeed",
            description="Search jobs on Indeed",
            category=SkillCategory.JOB_SEARCH,
            config={"max_results": 20}
        ))
        
        self.register(AgentSkill(
            name="job_search_naukri",
            description="Search jobs on Naukri",
            category=SkillCategory.JOB_SEARCH,
            config={"max_results": 20}
        ))
        
        self.register(AgentSkill(
            name="job_search_walkins",
            description="Find walk-in interview opportunities",
            category=SkillCategory.JOB_SEARCH
        ))
        
        # Resume Skills
        self.register(AgentSkill(
            name="resume_parse",
            description="Extract structured information from resume",
            category=SkillCategory.RESUME_PARSING
        ))
        
        self.register(AgentSkill(
            name="resume_match",
            description="Calculate ATS match score",
            category=SkillCategory.RESUME_PARSING
        ))
        
        # Application Skills
        self.register(AgentSkill(
            name="application_fill",
            description="Fill job application forms",
            category=SkillCategory.APPLICATION
        ))
        
        self.register(AgentSkill(
            name="application_submit",
            description="Submit job application",
            category=SkillCategory.APPLICATION
        ))
        
        # Outreach Skills
        self.register(AgentSkill(
            name="outreach_find_contacts",
            description="Find company employees",
            category=SkillCategory.OUTREACH
        ))
        
        self.register(AgentSkill(
            name="outreach_generate_message",
            description="Generate personalized outreach messages",
            category=SkillCategory.OUTREACH
        ))
    
    def register(self, skill: AgentSkill):
        self.skills[skill.name] = skill
    
    def get_skill(self, name: str) -> Optional[AgentSkill]:
        return self.skills.get(name)
    
    def get_skills_by_category(self, category: SkillCategory) -> List[AgentSkill]:
        return [s for s in self.skills.values() if s.category == category]
    
    def get_skill_manifest(self) -> Dict[str, Any]:
        return {
            name: {
                "description": skill.description,
                "category": skill.category.value,
                "enabled": skill.enabled
            }
            for name, skill in self.skills.items()
        }


skills_registry = AISkillsRegistry()