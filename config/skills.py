"""Shared skill keywords for resume matching and ATS scoring."""

# Priority skills (Appian/BPM - checked first in resume analysis)
PRIORITY_SKILLS = [
    "appian", "bpm", "sail", "cdt", "smart services", "process models",
    "record types", "data stores", "process flows", "action interfaces",
    "bpmn", "process model", "record type", "data store", "smart service",
]

# Core technical skills
SKILL_KEYWORDS = [
    # Languages
    "java", "python", "sql", "javascript", "typescript", "html", "css",
    "c++", "c#", ".net", "php", "ruby", "golang", "go", "rust", "kotlin", "swift",
    # Frontend
    "react", "angular", "vue", "svelte", "next", "nuxt", "node.js", "nodejs",
    # Backend
    "spring boot", "spring", "django", "flask", "fastapi", "express",
    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "ci/cd", "github actions", "cloud",
    # Databases
    "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
    "oracle", "sqlite", "cassandra",
    # AI/ML
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "scikit-learn", "scikit", "pandas", "numpy",
    "data science", "data analysis", "data visualization",
    # Tools
    "git", "github", "jira", "confluence", "agile", "scrum",
    # Testing
    "selenium", "cypress", "jest", "mocha", "junit", "pytest", "testing", "unit testing",
    # APIs
    "rest api", "rest", "restful", "graphql", "microservices", "soap", "api", "integration",
    # IoT/Embedded
    "arduino", "iot", "embedded systems", "raspberry pi",
    # Security
    "cybersecurity", "networking", "linux", "bash", "shell scripting", "powershell",
    # Enterprise
    "sap", "salesforce", "servicenow", "workday", "pega",
    # Design
    "ui/ux", "figma", "sketch", "adobe", "photoshop", "illustrator",
    # Mobile
    "android", "ios", "flutter", "react native", "dart",
    # Infrastructure
    "kafka", "rabbitmq", "nginx", "apache", "tomcat",
    "windows server", "active directory",
    # Industrial
    "cnc", "plc", "scada", "industrial automation",
    # Analytics
    "tableau", "power bi", "excel",
]

# Combined list for matching (priority first, then rest)
ALL_SKILLS = PRIORITY_SKILLS + [s for s in SKILL_KEYWORDS if s not in PRIORITY_SKILLS]
