"""
config.py - API keys, database settings, and constants
"""

import os
from dotenv import load_dotenv
from typing import Dict, List

# Load environment variables
load_dotenv()


class Settings:
    """Application settings and configuration."""
    
    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Groq Model Settings
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_EMBEDDING_MODEL: str = "llama-3.1-8b-instant"
    
    # Chroma DB Settings
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    CHROMA_COLLECTION_NAME: str = "resumes"
    
    # RAG Settings
    CHUNK_SIZE: int = 500  # tokens
    CHUNK_OVERLAP: int = 50
    TOP_K_CHUNKS: int = 5  # chunks to retrieve per query
    MAX_RESUMES_PER_JD: int = 50
    
    # Scoring Weights
    SCORING_WEIGHTS: Dict[str, float] = {
        "skills": 0.50,
        "experience": 0.30,
        "education": 0.20
    }
    
    # Role Levels
    ROLE_LEVELS: List[str] = ["Intern", "Junior", "Mid", "Senior", "Lead"]
    
    # Recommendation Thresholds
    RECOMMENDATION_THRESHOLDS: Dict[str, float] = {
        "strong_fit": 75.0,
        "partial_fit": 50.0,
        "weak_fit": 0.0
    }
    
    # Skill Synonyms for Normalization
    SKILL_SYNONYMS: Dict[str, str] = {
        "js": "JavaScript",
        "javascript": "JavaScript",
        "ts": "TypeScript",
        "typescript": "TypeScript",
        "py": "Python",
        "python": "Python",
        "react.js": "React",
        "reactjs": "React",
        "react": "React",
        "node.js": "Node.js",
        "nodejs": "Node.js",
        "node": "Node.js",
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "mongo": "MongoDB",
        "mongodb": "MongoDB",
        "aws": "AWS",
        "amazon web services": "AWS",
        "gcp": "Google Cloud Platform",
        "google cloud": "Google Cloud Platform",
        "k8s": "Kubernetes",
        "kubernetes": "Kubernetes",
        "docker": "Docker",
        "ml": "Machine Learning",
        "machine learning": "Machine Learning",
        "ai": "Artificial Intelligence",
        "artificial intelligence": "Artificial Intelligence",
        "dl": "Deep Learning",
        "deep learning": "Deep Learning",
        "sql": "SQL",
        "mysql": "MySQL",
        "c#": "C#",
        "csharp": "C#",
        "c++": "C++",
        "cpp": "C++",
        "golang": "Go",
        "go": "Go",
        "tf": "TensorFlow",
        "tensorflow": "TensorFlow",
        "pytorch": "PyTorch",
        "vue.js": "Vue.js",
        "vuejs": "Vue.js",
        "vue": "Vue.js",
        "angular.js": "Angular",
        "angularjs": "Angular",
        "angular": "Angular",
        "java": "Java",
        "spring": "Spring Framework",
        "spring boot": "Spring Boot",
        "springboot": "Spring Boot",
        "fastapi": "FastAPI",
        "flask": "Flask",
        "django": "Django",
        "express": "Express.js",
        "expressjs": "Express.js",
        "express.js": "Express.js",
        "graphql": "GraphQL",
        "rest": "REST API",
        "restful": "REST API",
        "rest api": "REST API",
        "ci/cd": "CI/CD",
        "cicd": "CI/CD",
        "git": "Git",
        "github": "GitHub",
        "gitlab": "GitLab",
        "jenkins": "Jenkins",
        "terraform": "Terraform",
        "ansible": "Ansible",
        "linux": "Linux",
        "unix": "Unix",
        "bash": "Bash",
        "shell": "Shell Scripting",
        "agile": "Agile",
        "scrum": "Scrum",
    }
    
    # Common degree patterns
    DEGREE_PATTERNS: Dict[str, List[str]] = {
        "phd": ["phd", "ph.d", "doctorate", "doctor of philosophy"],
        "masters": ["master", "ms", "m.s.", "msc", "m.sc", "mba", "m.b.a", "mtech", "m.tech"],
        "bachelors": ["bachelor", "bs", "b.s.", "bsc", "b.sc", "btech", "b.tech", "ba", "b.a."],
        "associate": ["associate", "as", "a.s.", "aa", "a.a."],
        "diploma": ["diploma", "certificate", "certification"]
    }


# Global settings instance
settings = Settings()