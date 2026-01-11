"""
resume_parser.py - Resume parsing and structured data extraction
"""

import re
import logging
import json
from typing import Dict, List, Optional, Any
from utils import (
    extract_email, extract_phone, extract_years_of_experience,
    clean_text
)
from config import settings
from groq import Groq

logger = logging.getLogger(__name__)


class ResumeParser:
    """Parse resume text and extract structured candidate information."""
    
    # Common skill patterns
    SKILL_KEYWORDS = [
        # Programming Languages
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "Ruby", "PHP",
        "Swift", "Kotlin", "Scala", "R", "MATLAB", "SQL", "HTML", "CSS",
        # Frameworks & Libraries
        "React", "Angular", "Vue", "Node.js", "Express", "Django", "Flask", "FastAPI",
        "Spring", "Laravel", "ASP.NET", "Next.js", "Nuxt", "Svelte",
        # Databases
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Cassandra", "Elasticsearch",
        # Cloud & DevOps
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Jenkins", "CI/CD", "Terraform",
        # Tools & Technologies
        "Git", "Linux", "Agile", "Scrum", "JIRA", "Confluence"
    ]
    
    # Education patterns
    EDUCATION_PATTERNS = [
        r'\b(B\.?S\.?|B\.?A\.?|B\.?Tech|Bachelor)\b',
        r'\b(M\.?S\.?|M\.?A\.?|M\.?Tech|M\.?B\.?A\.?|Master)\b',
        r'\b(Ph\.?D\.?|Doctorate|PhD)\b',
        r'\b(Associate|Diploma|Certificate)\b'
    ]

    def __init__(self):
        self.groq_client = None
        if settings.GROQ_API_KEY:
            self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
    
    def parse(self, resume_text: str, candidate_name: str) -> Dict[str, Any]:
        """
        Parse resume text and extract structured information.
        
        Args:
            resume_text: Raw resume text
            candidate_name: Candidate's name
            
        Returns:
            Dictionary with parsed candidate data
        """
        # Clean text
        text = clean_text(resume_text)
        text_lower = text.lower()
        
        # Extract basic information
        email = extract_email(text)
        phone = extract_phone(text)
        experience_years = extract_years_of_experience(text)
        
        # Extract skills
        skills = self._extract_skills(text, text_lower)
        
        # Extract education
        education = self._extract_education(text, text_lower)
        
        # Extract experience summary (first few lines or summary section)
        experience_summary = self._extract_experience_summary(text)
        
        return {
            "name": candidate_name,
            "email": email or "",
            "phone": phone or "",
            "experience_years": experience_years or 0,
            "experience_summary": experience_summary,
            "skills": skills,
            "education": education,
            "raw_text": resume_text
        }
    
    def _extract_skills(self, text: str, text_lower: str) -> List[str]:
        """Extract skills from resume text."""
        found_skills = set()
        
        # Check for skills section
        skills_section_patterns = [
            r'skills?\s*:?\s*([^\n]+(?:\n[^\n]+){0,10})',
            r'technical\s+skills?\s*:?\s*([^\n]+(?:\n[^\n]+){0,10})',
            r'competencies?\s*:?\s*([^\n]+(?:\n[^\n]+){0,10})'
        ]
        
        skills_text = ""
        for pattern in skills_section_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
            if match:
                skills_text = match.group(1)
                break
        
        # If no skills section found, search entire text
        if not skills_text:
            skills_text = text
        
        # Find known skills
        for skill in self.SKILL_KEYWORDS:
            if re.search(r'\b' + re.escape(skill.lower()) + r'\b', skills_text, re.IGNORECASE):
                found_skills.add(skill)
        
        # Also look for common skill patterns (words that appear frequently)
        # Extract capitalized words/phrases that might be skills
        capitalized_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        potential_skills = re.findall(capitalized_pattern, skills_text)
        
        # Filter potential skills (common technical terms)
        for skill_candidate in potential_skills:
            skill_lower = skill_candidate.lower()
            # Common technical terms
            if any(keyword in skill_lower for keyword in [
                'api', 'framework', 'library', 'database', 'server',
                'cloud', 'devops', 'frontend', 'backend', 'fullstack'
            ]):
                if len(skill_candidate) > 2 and len(skill_candidate) < 30:
                    found_skills.add(skill_candidate)
        
        return sorted(list(found_skills))
    
    def _extract_education(self, text: str, text_lower: str) -> List[str]:
        """Extract education information."""
        education_items = []
        
        # Look for education section
        education_section_patterns = [
            r'education\s*:?\s*([^\n]+(?:\n[^\n]+){0,10})',
            r'academic\s+background\s*:?\s*([^\n]+(?:\n[^\n]+){0,10})'
        ]
        
        education_text = ""
        for pattern in education_section_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
            if match:
                education_text = match.group(1)
                break
        
        # If no education section, search entire text
        if not education_text:
            education_text = text
        
        # Extract degree types
        for pattern in self.EDUCATION_PATTERNS:
            matches = re.finditer(pattern, education_text, re.IGNORECASE)
            for match in matches:
                # Get context around the match (degree name)
                start = max(0, match.start() - 50)
                end = min(len(education_text), match.end() + 100)
                context = education_text[start:end].strip()
                
                # Extract degree line
                lines = context.split('\n')
                for line in lines:
                    if match.group(0).lower() in line.lower():
                        cleaned = line.strip()
                        if cleaned and cleaned not in education_items:
                            education_items.append(cleaned)
                            break
        
        return education_items[:5]  # Limit to 5 items
    
    def _extract_experience_summary(self, text: str) -> str:
        """Extract experience summary from resume."""
        # Look for summary/objective section
        summary_patterns = [
            r'summary\s*:?\s*([^\n]+(?:\n[^\n]+){0,5})',
            r'objective\s*:?\s*([^\n]+(?:\n[^\n]+){0,5})',
            r'profile\s*:?\s*([^\n]+(?:\n[^\n]+){0,5})',
            r'about\s*:?\s*([^\n]+(?:\n[^\n]+){0,5})'
        ]
        
        text_lower = text.lower()
        for pattern in summary_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
            if match:
                summary = match.group(1).strip()
                # Clean up summary
                summary = re.sub(r'\s+', ' ', summary)
                if len(summary) > 50:  # Valid summary
                    return summary[:500]  # Limit length
        
        # If no summary found, use first 300 characters
        cleaned = re.sub(r'\s+', ' ', text.strip())
        return cleaned[:300] + "..." if len(cleaned) > 300 else cleaned

    def parse_with_llm(self, resume_text: str) -> Dict[str, Any]:
        """Parse resume using Groq LLM for better accuracy."""
        if not self.groq_client:
            logger.warning("Groq client not initialized, falling back to regex parser")
            return self.parse(resume_text, "Unknown")

        prompt = f"""
        Extract structured information from the following resume text.
        
        RESUME TEXT:
        {resume_text[:4000]}
        
        Provide the output in this EXACT JSON format:
        {{
            "candidate_name": "Full Name",
            "skills": ["Skill1", "Skill2", ...],
            "experience": "Brief experience summary (e.g. 3+ years in backend)",
            "education": "Highest degree (e.g. B.Tech in CS)",
            "email": "email@example.com",
            "phone": "phone number"
        }}
        
        Return ONLY the JSON object.
        """
        
        try:
            response = self.groq_client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            content = response.choices[0].message.content.strip()
            
            # Clean potential markdown
            if content.startswith("```"):
                content = re.sub(r'^```json?\n?', '', content)
                content = re.sub(r'\n?```$', '', content)
            
            return json.loads(content)
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            return self.parse(resume_text, "Unknown")
