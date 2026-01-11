"""
schemas.py - Pydantic models for request and response JSON
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


# ==================== Enums ====================

class RoleLevel(str, Enum):
    INTERN = "Intern"
    JUNIOR = "Junior"
    MID = "Mid"
    SENIOR = "Senior"
    LEAD = "Lead"


class Recommendation(str, Enum):
    STRONG_FIT = "Strong Fit"
    PARTIAL_FIT = "Partial Fit"
    WEAK_FIT = "Weak Fit"


# ==================== Request Models ====================

class JobDescriptionInput(BaseModel):
    """Input model for job description."""
    job_id: Optional[str] = Field(default=None, description="Unique job identifier")
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Full job description text")
    mandatory_skills: Optional[List[str]] = Field(default=[], description="List of required skills")
    optional_skills: Optional[List[str]] = Field(default=[], description="List of nice-to-have skills")
    min_experience_years: Optional[int] = Field(default=0, description="Minimum years of experience")
    education_requirements: Optional[str] = Field(default=None, description="Education requirements")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "JD-001",
                "title": "Senior Python Developer",
                "description": "We are looking for a Senior Python Developer with 5+ years of experience...",
                "mandatory_skills": ["Python", "FastAPI", "PostgreSQL"],
                "optional_skills": ["Docker", "AWS", "Redis"],
                "min_experience_years": 5,
                "education_requirements": "Bachelor's degree in Computer Science or related field"
            }
        }


class ResumeInput(BaseModel):
    """Input model for a single resume."""
    candidate_id: str = Field(..., description="Unique candidate identifier")
    candidate_name: str = Field(..., description="Candidate's full name")
    resume_text: str = Field(..., description="Full text content of the resume")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")
    
    @validator('metadata')
    def validate_pdf_file(cls, v):
        """Validate that the resume file is a PDF (if metadata is provided)."""
        # Allow empty metadata dict
        if not v:
            return {}
        
        # If metadata is provided, validate PDF fields (but don't require them)
        file_type = v.get('file_type', '').lower()
        file_extension = v.get('file_extension', '').lower()
        
        # Only validate if file_type is provided
        if file_type and file_type != 'application/pdf':
            raise ValueError(f"Invalid file type: {file_type}. Only PDF files (application/pdf) are accepted.")
        
        # Only validate if file_extension is provided
        if file_extension and file_extension != '.pdf':
            raise ValueError(f"Invalid file extension: {file_extension}. Only .pdf files are accepted.")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "CAND-001",
                "candidate_name": "John Doe",
                "resume_text": "Experienced software developer with 6 years of Python experience...",
                "metadata": {
                    "file_type": "application/pdf",
                    "file_extension": ".pdf",
                    "file_name": "resume.pdf",
                    "file_size": 12345
                }
            }
        }


class BulkResumeInput(BaseModel):
    """Input model for bulk resume upload."""
    job_id: str = Field(..., description="Associated job ID")
    resumes: List[ResumeInput] = Field(..., description="List of resumes")
    
    @validator('resumes')
    def validate_resume_count(cls, v):
        if len(v) > 50:
            raise ValueError("Maximum 50 resumes allowed per batch")
        return v


class EvaluationRequest(BaseModel):
    """Request model for evaluation."""
    job_id: str = Field(..., description="Job ID to evaluate against")
    candidate_ids: Optional[List[str]] = Field(default=None, description="Specific candidates to evaluate")


# ==================== Response Models ====================

class ScoreBreakdown(BaseModel):
    """Score breakdown for a candidate."""
    skills_score: float = Field(..., ge=0, le=100, description="Skills match score (0-100)")
    experience_score: float = Field(..., ge=0, le=100, description="Experience relevance score (0-100)")
    education_score: float = Field(..., ge=0, le=100, description="Education score (0-100)")
    final_score: float = Field(..., ge=0, le=100, description="Weighted final score (0-100)")


class CandidateEvaluation(BaseModel):
    """Evaluation result for a single candidate."""
    candidate_id: str = Field(..., description="Unique candidate identifier")
    candidate_name: str = Field(..., description="Candidate's full name")
    role_level: RoleLevel = Field(..., description="Inferred role level from JD")
    scores: ScoreBreakdown = Field(..., description="Score breakdown")
    matched_skills: List[str] = Field(default=[], description="Skills found in resume matching JD")
    missing_skills: List[str] = Field(default=[], description="Required skills missing from resume")
    relevant_experience: str = Field(default="", description="Summary of relevant experience")
    strengths: List[str] = Field(default=[], description="Key strengths identified")
    weaknesses: List[str] = Field(default=[], description="Areas of concern")
    overall_recommendation: Recommendation = Field(..., description="Fit recommendation")
    confidence_notes: str = Field(default="", description="Justification based on resume evidence")
    
    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "CAND-001",
                "candidate_name": "John Doe",
                "role_level": "Senior",
                "scores": {
                    "skills_score": 85.0,
                    "experience_score": 80.0,
                    "education_score": 90.0,
                    "final_score": 84.5
                },
                "matched_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                "missing_skills": ["AWS"],
                "relevant_experience": "6 years of Python development with focus on backend APIs",
                "strengths": ["Strong Python expertise", "API development experience"],
                "weaknesses": ["Limited cloud experience"],
                "overall_recommendation": "Strong Fit",
                "confidence_notes": "Candidate shows strong alignment with core requirements."
            }
        }


class EvaluationResponse(BaseModel):
    """Response model for evaluation results."""
    job_id: str = Field(..., description="Job ID evaluated")
    job_title: str = Field(..., description="Job title")
    role_level: RoleLevel = Field(..., description="Inferred role level")
    total_candidates: int = Field(..., description="Total candidates evaluated")
    evaluation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    candidates: List[CandidateEvaluation] = Field(..., description="Ranked candidate evaluations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "JD-001",
                "job_title": "Senior Python Developer",
                "role_level": "Senior",
                "total_candidates": 25,
                "evaluation_timestamp": "2024-01-15T10:30:00Z",
                "candidates": []
            }
        }


class UploadResponse(BaseModel):
    """Response for upload operations."""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Status message")
    job_id: Optional[str] = Field(default=None, description="Job ID if applicable")
    count: Optional[int] = Field(default=None, description="Number of items processed")


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: bool = Field(default=True)
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field(default="healthy")
    version: str = Field(default="1.0.0")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = Field(default={})


class CandidateProfile(BaseModel):
    """Parsed candidate profile data."""
    candidate_id: str = Field(..., description="Unique candidate identifier")
    job_id: str = Field(..., description="Job ID this candidate is associated with")
    name: str = Field(..., description="Candidate's full name")
    email: str = Field(default="", description="Candidate's email")
    phone: str = Field(default="", description="Candidate's phone number")
    experience_years: int = Field(default=0, description="Years of experience")
    experience_summary: str = Field(default="", description="Experience summary")
    skills: List[str] = Field(default=[], description="List of skills")
    education: List[str] = Field(default=[], description="Education details")
    raw_text: str = Field(default="", description="Original resume text")


class CandidateDetailResponse(BaseModel):
    """Detailed candidate response."""
    candidate_id: str = Field(..., description="Unique candidate identifier")
    name: str = Field(..., description="Candidate's full name")
    email: str = Field(default="", description="Candidate's email")
    phone: str = Field(default="", description="Candidate's phone number")
    experience_years: int = Field(default=0, description="Years of experience")
    experience_summary: str = Field(default="", description="Experience summary")
    skills: List[str] = Field(default=[], description="List of skills")
    education: List[str] = Field(default=[], description="Education details")
    matched_skills: List[str] = Field(default=[], description="Skills matching job description")
    missing_skills: List[str] = Field(default=[], description="Skills missing from resume")
    match_percentage: float = Field(default=0.0, ge=0, le=100, description="Skill match percentage")


class CompareRequest(BaseModel):
    """Request model for candidate comparison."""
    job_id: str = Field(..., description="Job ID")
    candidate_ids: List[str] = Field(..., min_items=2, description="List of candidate IDs to compare")


class CompareResponse(BaseModel):
    """Response model for candidate comparison."""
    job_id: str = Field(..., description="Job ID")
    candidates: List[CandidateDetailResponse] = Field(..., description="List of compared candidates")


class AnalyzeResumeResponse(BaseModel):
    """Exact response model required by user for resume analysis."""
    candidate_id: str = Field(..., description="Unique candidate identifier")
    name: str = Field(..., description="Candidate's full name")
    skills: List[str] = Field(..., description="Extracted skills")
    missing_skills: List[str] = Field(..., description="Missing skills vs JD")
    experience: str = Field(..., description="Experience summary")
    education: str = Field(..., description="Education summary")
    match_score: int = Field(..., description="Skill match score (0-100)")


class AnalyzeResumeRequest(BaseModel):
    """Request model for one-shot resume analysis."""
    job_id: Optional[str] = Field(None, description="Job ID")
    jd_text: str = Field(..., description="Job description text")
    candidate_name: Optional[str] = Field(None, description="Candidate name if known")


# ==================== Strict Output Models ====================

class SkillsBreakdown(BaseModel):
    matched: List[str]
    missing: List[str]
    partial: List[str]

class ExperienceBreakdown(BaseModel):
    required_years: Optional[int]
    candidate_years: Optional[int]
    match: str

class EducationBreakdown(BaseModel):
    required: Optional[str]
    candidate: Optional[str]
    match: str

class StrictEvaluationResponse(BaseModel):
    candidate_id: str
    candidate_name: str
    job_id: str
    overall_match_score: float
    skills: SkillsBreakdown
    experience: ExperienceBreakdown
    education: EducationBreakdown
    strengths: List[str]
    gaps: List[str]
    summary: str
    recommendation: str  # "Strong Fit" | "Moderate Fit" | "Weak Fit"

class ComparisonRankingItem(BaseModel):
    candidate_name: str
    match_score: float
    key_advantages: List[str]
    key_gaps: List[str]

class StrictComparisonResponse(BaseModel):
    job_id: str
    ranking: List[ComparisonRankingItem]
    best_candidate: str