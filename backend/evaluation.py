"""
evaluation.py - Candidate scoring logic
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from config import settings
from schemas import (
    RoleLevel, Recommendation, ScoreBreakdown,
    CandidateEvaluation, JobDescriptionInput
)
from rag_utils import RAGProcessor


class RoleLevelInferrer:
    """Infers role level from job description."""
    
    LEVEL_INDICATORS = {
        RoleLevel.INTERN: {
            "keywords": ["intern", "internship", "trainee", "student", "entry-level"],
            "experience_years": (0, 1),
            "weight": 1
        },
        RoleLevel.JUNIOR: {
            "keywords": ["junior", "associate", "graduate", "entry level", "0-2 years", "1-2 years", "fresher"],
            "experience_years": (0, 2),
            "weight": 2
        },
        RoleLevel.MID: {
            "keywords": ["mid-level", "mid level", "intermediate", "3-5 years", "2-4 years", "3+ years"],
            "experience_years": (2, 5),
            "weight": 3
        },
        RoleLevel.SENIOR: {
            "keywords": ["senior", "sr.", "experienced", "5+ years", "5-8 years", "7+ years", "expert"],
            "experience_years": (5, 10),
            "weight": 4
        },
        RoleLevel.LEAD: {
            "keywords": ["lead", "principal", "staff", "architect", "manager", "head", "director", "10+ years"],
            "experience_years": (8, 20),
            "weight": 5
        }
    }
    
    def infer_role_level(self, jd: JobDescriptionInput) -> RoleLevel:
        """Infer role level from job description."""
        jd_text = f"{jd.title} {jd.description}".lower()
        
        level_scores = {}
        
        for level, indicators in self.LEVEL_INDICATORS.items():
            score = 0
            
            # Check keywords
            for keyword in indicators["keywords"]:
                if keyword in jd_text:
                    score += 2
            
            # Check experience years
            if jd.min_experience_years is not None:
                min_exp, max_exp = indicators["experience_years"]
                if min_exp <= jd.min_experience_years <= max_exp:
                    score += 3
            
            level_scores[level] = score
        
        # Return level with highest score, default to Mid if no clear match
        if max(level_scores.values()) == 0:
            return RoleLevel.MID
        
        return max(level_scores, key=level_scores.get)


class SkillNormalizer:
    """Normalizes skill names for consistent matching."""
    
    def __init__(self):
        self.synonyms = {k.lower(): v for k, v in settings.SKILL_SYNONYMS.items()}
    
    def normalize(self, skill: str) -> str:
        """Normalize a skill name."""
        skill_lower = skill.lower().strip()
        return self.synonyms.get(skill_lower, skill.strip())
    
    def normalize_list(self, skills: List[str]) -> List[str]:
        """Normalize a list of skills and remove duplicates."""
        normalized = set()
        for skill in skills:
            normalized.add(self.normalize(skill))
        return list(normalized)
    
    def extract_skills_from_text(self, text: str, reference_skills: List[str]) -> List[str]:
        """Extract skills from text that match reference skills."""
        text_lower = text.lower()
        found_skills = set()
        
        for skill in reference_skills:
            skill_normalized = self.normalize(skill)
            skill_lower = skill_normalized.lower()
            
            # Check for exact match or word boundary match
            pattern = r'\b' + re.escape(skill_lower) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill_normalized)
            
            # Also check for the original skill
            if skill.lower() in text_lower:
                found_skills.add(skill_normalized)
        
        return list(found_skills)


class ScoreCalculator:
    """Calculates scores for candidates."""
    
    def __init__(self):
        self.weights = settings.SCORING_WEIGHTS
        self.thresholds = settings.RECOMMENDATION_THRESHOLDS
    
    def calculate_skills_score(
        self,
        matched_skills: List[str],
        missing_skills: List[str],
        mandatory_skills: List[str],
        optional_skills: List[str]
    ) -> float:
        """Calculate skills match score."""
        if not mandatory_skills and not optional_skills:
            return 50.0  # Default if no skills specified
        
        total_mandatory = len(mandatory_skills)
        total_optional = len(optional_skills)
        
        # Normalize all skills for comparison
        normalizer = SkillNormalizer()
        matched_normalized = set(normalizer.normalize(s) for s in matched_skills)
        mandatory_normalized = set(normalizer.normalize(s) for s in mandatory_skills)
        optional_normalized = set(normalizer.normalize(s) for s in optional_skills)
        
        # Count matches
        mandatory_matched = len(matched_normalized.intersection(mandatory_normalized))
        optional_matched = len(matched_normalized.intersection(optional_normalized))
        
        # Mandatory skills are worth 70% of skills score
        mandatory_score = 0
        if total_mandatory > 0:
            mandatory_score = (mandatory_matched / total_mandatory) * 70
        else:
            mandatory_score = 70  # Full marks if no mandatory skills
        
        # Optional skills are worth 30% of skills score
        optional_score = 0
        if total_optional > 0:
            optional_score = (optional_matched / total_optional) * 30
        else:
            optional_score = 30  # Full marks if no optional skills
        
        # Heavy penalty for missing mandatory skills
        missing_mandatory = total_mandatory - mandatory_matched
        penalty = missing_mandatory * 10  # 10 points penalty per missing mandatory skill
        
        final_score = max(0, (mandatory_score + optional_score) - penalty)
        return min(100, final_score)
    
    def calculate_final_score(self, scores: ScoreBreakdown) -> float:
        """Calculate weighted final score."""
        final = (
            scores.skills_score * self.weights["skills"] +
            scores.experience_score * self.weights["experience"] +
            scores.education_score * self.weights["education"]
        )
        return round(final, 2)
    
    def determine_recommendation(self, final_score: float) -> Recommendation:
        """Determine recommendation based on final score."""
        if final_score >= self.thresholds["strong_fit"]:
            return Recommendation.STRONG_FIT
        elif final_score >= self.thresholds["partial_fit"]:
            return Recommendation.PARTIAL_FIT
        else:
            return Recommendation.WEAK_FIT


class CandidateEvaluator:
    """Main candidate evaluation orchestrator."""
    
    def __init__(self):
        self.rag_processor = RAGProcessor()
        self.role_inferrer = RoleLevelInferrer()
        self.skill_normalizer = SkillNormalizer()
        self.score_calculator = ScoreCalculator()
    
    def evaluate_candidates(
        self,
        jd: JobDescriptionInput,
        candidate_ids: Optional[List[str]] = None
    ) -> List[CandidateEvaluation]:
        """Evaluate all candidates for a job."""
        
        # Infer role level from JD
        role_level = self.role_inferrer.infer_role_level(jd)
        
        # Normalize skills
        mandatory_skills = self.skill_normalizer.normalize_list(jd.mandatory_skills or [])
        optional_skills = self.skill_normalizer.normalize_list(jd.optional_skills or [])
        all_skills = mandatory_skills + optional_skills
        
        # Get candidates
        candidates = self.rag_processor.get_all_candidates_for_job(jd.job_id)
        
        # Filter if specific candidates requested
        if candidate_ids:
            candidates = [c for c in candidates if c["candidate_id"] in candidate_ids]
        
        # Limit to max resumes
        candidates = candidates[:settings.MAX_RESUMES_PER_JD]
        
        # Evaluate each candidate
        evaluations = []
        jd_text = f"Title: {jd.title}\n\nDescription: {jd.description}"
        
        if jd.education_requirements:
            jd_text += f"\n\nEducation Requirements: {jd.education_requirements}"
        
        for candidate in candidates:
            evaluation = self._evaluate_single_candidate(
                jd=jd,
                jd_text=jd_text,
                candidate=candidate,
                role_level=role_level,
                mandatory_skills=mandatory_skills,
                optional_skills=optional_skills,
                all_skills=all_skills
            )
            evaluations.append(evaluation)
        
        # Sort by final score (descending)
        evaluations.sort(key=lambda x: x.scores.final_score, reverse=True)
        
        return evaluations
    
    def _evaluate_single_candidate(
        self,
        jd: JobDescriptionInput,
        jd_text: str,
        candidate: Dict[str, Any],
        role_level: RoleLevel,
        mandatory_skills: List[str],
        optional_skills: List[str],
        all_skills: List[str]
    ) -> CandidateEvaluation:
        """Evaluate a single candidate."""
        
        candidate_id = candidate["candidate_id"]
        candidate_name = candidate["candidate_name"]
        
        # Get candidate context from RAG
        context, chunks = self.rag_processor.get_candidate_context(
            job_id=jd.job_id,
            candidate_id=candidate_id,
            jd_text=jd_text
        )
        
        # Use LLM for evaluation if we have context
        if context:
            llm_evaluation = self.rag_processor.evaluate_with_llm(
                jd_text=jd_text,
                candidate_context=context,
                candidate_name=candidate_name,
                mandatory_skills=mandatory_skills,
                optional_skills=optional_skills
            )
        else:
            # No context available
            llm_evaluation = {
                "matched_skills": [],
                "missing_skills": mandatory_skills,
                "skills_score": 0,
                "experience_summary": "No resume content available",
                "experience_score": 0,
                "education_details": "Unknown",
                "education_score": 0,
                "strengths": [],
                "weaknesses": ["No resume data found"],
                "confidence_notes": "Unable to evaluate - no resume content retrieved"
            }
        
        # Normalize matched skills
        matched_skills = self.skill_normalizer.normalize_list(
            llm_evaluation.get("matched_skills", [])
        )
        
        # Calculate missing skills
        matched_set = set(s.lower() for s in matched_skills)
        missing_skills = [
            s for s in mandatory_skills 
            if s.lower() not in matched_set
        ]
        
        # Get scores from LLM evaluation or calculate
        skills_score = float(llm_evaluation.get("skills_score", 0))
        experience_score = float(llm_evaluation.get("experience_score", 0))
        education_score = float(llm_evaluation.get("education_score", 0))
        
        # Recalculate skills score if needed (for consistency)
        if matched_skills or mandatory_skills:
            skills_score = self.score_calculator.calculate_skills_score(
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                mandatory_skills=mandatory_skills,
                optional_skills=optional_skills
            )
        
        # Build score breakdown
        scores = ScoreBreakdown(
            skills_score=round(skills_score, 2),
            experience_score=round(experience_score, 2),
            education_score=round(education_score, 2),
            final_score=0  # Will be calculated
        )
        
        # Calculate final score
        scores.final_score = self.score_calculator.calculate_final_score(scores)
        
        # Determine recommendation
        recommendation = self.score_calculator.determine_recommendation(scores.final_score)
        
        # Build evaluation result
        evaluation = CandidateEvaluation(
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            role_level=role_level,
            scores=scores,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            relevant_experience=llm_evaluation.get("experience_summary", ""),
            strengths=llm_evaluation.get("strengths", []),
            weaknesses=llm_evaluation.get("weaknesses", []),
            overall_recommendation=recommendation,
            confidence_notes=llm_evaluation.get("confidence_notes", "")
        )
        
        return evaluation
    
    def evaluate_single(
        self,
        jd: JobDescriptionInput,
        candidate_id: str
    ) -> Optional[CandidateEvaluation]:
        """Evaluate a single specific candidate."""
        evaluations = self.evaluate_candidates(jd, candidate_ids=[candidate_id])
        return evaluations[0] if evaluations else None