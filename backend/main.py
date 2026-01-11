"""
main.py - FastAPI app and endpoints
"""
import re
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager
from io import BytesIO

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from schemas import (
    JobDescriptionInput, ResumeInput, BulkResumeInput,
    EvaluationRequest, EvaluationResponse, CandidateEvaluation,
    UploadResponse, ErrorResponse, HealthCheckResponse,
    CandidateProfile, CandidateDetailResponse, CompareRequest, CompareResponse,
    AnalyzeResumeResponse, AnalyzeResumeRequest,
    StrictEvaluationResponse, StrictComparisonResponse
)
from evaluation import CandidateEvaluator
from rag_utils import RAGProcessor
from utils import generate_job_id, generate_candidate_id, RateLimiter
from pdf_extractor import PDFExtractor
from resume_parser import ResumeParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== Application State ====================

class AppState:
    """Application state container."""
    
    def __init__(self):
        self.rag_processor: Optional[RAGProcessor] = None
        self.evaluator: Optional[CandidateEvaluator] = None
        self.job_descriptions: Dict[str, JobDescriptionInput] = {}
        self.rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
        self.evaluation_cache: Dict[str, EvaluationResponse] = {}
        # Store parsed candidate profiles: {job_id: {candidate_id: CandidateProfile}}
        self.candidate_profiles: Dict[str, Dict[str, CandidateProfile]] = {}

app_state = AppState()


# ==================== Lifespan Management ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting ATS Evaluation Engine...")
    
    try:
        app_state.rag_processor = RAGProcessor()
        app_state.evaluator = CandidateEvaluator()
        logger.info("Initialized RAG processor and evaluator")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down ATS Evaluation Engine...")


# ==================== FastAPI App ====================

app = FastAPI(
    title="ATS Evaluation Engine",
    description="AI-powered Applicant Tracking System evaluation backend using RAG + Groq",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Exception Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=True,
            message=exc.detail
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=True,
            message="Internal server error",
            details={"type": type(exc).__name__}
        ).model_dump()
    )


# ==================== Dependencies ====================

async def get_rag_processor() -> RAGProcessor:
    """Dependency to get RAG processor."""
    if app_state.rag_processor is None:
        raise HTTPException(status_code=503, detail="RAG processor not initialized")
    return app_state.rag_processor


async def get_evaluator() -> CandidateEvaluator:
    """Dependency to get evaluator."""
    if app_state.evaluator is None:
        raise HTTPException(status_code=503, detail="Evaluator not initialized")
    return app_state.evaluator


async def check_rate_limit(client_id: str = Query(default="default")):
    """Rate limiting dependency."""
    if not app_state.rate_limiter.is_allowed(client_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    return client_id


# ==================== Health Check Endpoints ====================

@app.get("/", response_model=HealthCheckResponse, tags=["Health"])
async def root():
    """Root endpoint / health check."""
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        services={
            "rag_processor": "active" if app_state.rag_processor else "inactive",
            "evaluator": "active" if app_state.evaluator else "inactive",
            "groq_api": "configured" if settings.GROQ_API_KEY else "not configured"
        }
    )


@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    return await root()


# ==================== Job Description Endpoints ====================

@app.post("/api/v1/jobs", response_model=UploadResponse, tags=["Jobs"])
async def create_job(
    jd: JobDescriptionInput,
    client_id: str = Depends(check_rate_limit)
):
    """
    Create a new job description.
    
    This endpoint stores the job description for later candidate evaluation.
    """
    try:
        # Generate job ID if not provided
        if not jd.job_id:
            jd.job_id = generate_job_id()
        
        # Store job description
        app_state.job_descriptions[jd.job_id] = jd
        
        logger.info(f"Created job: {jd.job_id} - {jd.title}")
        
        return UploadResponse(
            success=True,
            message=f"Job description created successfully",
            job_id=jd.job_id
        )
    
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/jobs/{job_id}", response_model=JobDescriptionInput, tags=["Jobs"])
async def get_job(job_id: str):
    """Get a job description by ID."""
    if job_id not in app_state.job_descriptions:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return app_state.job_descriptions[job_id]


@app.put("/api/v1/jobs/{job_id}", response_model=UploadResponse, tags=["Jobs"])
async def update_job(
    job_id: str,
    jd: JobDescriptionInput,
    client_id: str = Depends(check_rate_limit)
):
    """
    Update an existing job description.
    
    This endpoint updates the job description while preserving the job_id.
    """
    # If job not found, create it (upsert behavior)
    if job_id not in app_state.job_descriptions:
        logger.info(f"Job {job_id} not found on update, creating new.")
    
    try:
        # Ensure job_id matches
        jd.job_id = job_id
        
        # Update job description
        app_state.job_descriptions[job_id] = jd
        
        # Invalidate evaluation cache for this job
        cache_keys_to_remove = [key for key in app_state.evaluation_cache.keys() if key.startswith(f"{job_id}_")]
        for key in cache_keys_to_remove:
            del app_state.evaluation_cache[key]
        
        logger.info(f"Updated job: {job_id} - {jd.title}")
        
        return UploadResponse(
            success=True,
            message=f"Job description updated successfully",
            job_id=job_id
        )
    
    except Exception as e:
        logger.error(f"Failed to update job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/jobs", response_model=List[JobDescriptionInput], tags=["Jobs"])
async def list_jobs():
    """List all job descriptions."""
    return list(app_state.job_descriptions.values())


@app.delete("/api/v1/jobs/{job_id}", response_model=UploadResponse, tags=["Jobs"])
async def delete_job(
    job_id: str,
    rag_processor: RAGProcessor = Depends(get_rag_processor)
):
    """Delete a job description and associated data."""
    if job_id not in app_state.job_descriptions:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        # Delete from vector store
        collection_name = f"job_{job_id}_resumes"
        rag_processor.vector_store.delete_collection(collection_name)
        
        # Delete from state
        del app_state.job_descriptions[job_id]
        
        # Clear cache
        if job_id in app_state.evaluation_cache:
            del app_state.evaluation_cache[job_id]
        
        return UploadResponse(
            success=True,
            message="Job and associated data deleted successfully"
        )
    
    except Exception as e:
        logger.error(f"Failed to delete job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Resume Endpoints ====================

@app.post("/api/v1/jobs/{job_id}/resumes", response_model=UploadResponse, tags=["Resumes"])
async def upload_resume(
    job_id: str,
    resume: ResumeInput,
    rag_processor: RAGProcessor = Depends(get_rag_processor),
    client_id: str = Depends(check_rate_limit)
):
    """
    Upload a single resume for a job.
    
    The resume will be chunked and indexed for RAG-based evaluation.
    """
    if job_id not in app_state.job_descriptions:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        # Generate candidate ID if empty
        if not resume.candidate_id:
            resume.candidate_id = generate_candidate_id()
        
        # Index the resume
        chunk_count = rag_processor.index_resume(
            job_id=job_id,
            candidate_id=resume.candidate_id,
            candidate_name=resume.candidate_name,
            resume_text=resume.resume_text,
            metadata=resume.metadata
        )
        
        # Invalidate cache for this job
        if job_id in app_state.evaluation_cache:
            del app_state.evaluation_cache[job_id]
        
        logger.info(f"Indexed resume: {resume.candidate_id} with {chunk_count} chunks")
        
        return UploadResponse(
            success=True,
            message=f"Resume indexed successfully with {chunk_count} chunks",
            job_id=job_id,
            count=chunk_count
        )
    
    except Exception as e:
        logger.error(f"Failed to upload resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/jobs/{job_id}/resumes/bulk", response_model=UploadResponse, tags=["Resumes"])
async def upload_resumes_bulk(
    job_id: str,
    bulk_input: BulkResumeInput,
    background_tasks: BackgroundTasks,
    rag_processor: RAGProcessor = Depends(get_rag_processor),
    client_id: str = Depends(check_rate_limit)
):
    """
    Upload multiple resumes for a job (up to 50).
    
    Resumes are processed, parsed, and indexed for RAG-based evaluation.
    """
    if job_id not in app_state.job_descriptions:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if len(bulk_input.resumes) > settings.MAX_RESUMES_PER_JD:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.MAX_RESUMES_PER_JD} resumes allowed per request"
        )
    
    try:
        parser = ResumeParser()
        total_chunks = 0
        processed = 0
        
        # Initialize candidate profiles dict for this job if not exists
        if job_id not in app_state.candidate_profiles:
            app_state.candidate_profiles[job_id] = {}
        
        for resume in bulk_input.resumes:
            # Generate candidate ID if empty
            if not resume.candidate_id:
                resume.candidate_id = generate_candidate_id()
            
            # Parse resume to extract structured data
            parsed_data = parser.parse(resume.resume_text, resume.candidate_name)
            
            # Create and store candidate profile
            candidate_profile = CandidateProfile(
                candidate_id=resume.candidate_id,
                job_id=job_id,
                name=parsed_data["name"],
                email=parsed_data.get("email", ""),
                phone=parsed_data.get("phone", ""),
                experience_years=parsed_data.get("experience_years", 0),
                experience_summary=parsed_data.get("experience_summary", ""),
                skills=parsed_data.get("skills", []),
                education=parsed_data.get("education", []),
                raw_text=resume.resume_text
            )
            app_state.candidate_profiles[job_id][resume.candidate_id] = candidate_profile
            
            # Index the resume for RAG
            chunk_count = rag_processor.index_resume(
                job_id=job_id,
                candidate_id=resume.candidate_id,
                candidate_name=resume.candidate_name,
                resume_text=resume.resume_text,
                metadata=resume.metadata
            )
            
            total_chunks += chunk_count
            processed += 1
        
        # Invalidate cache
        if job_id in app_state.evaluation_cache:
            del app_state.evaluation_cache[job_id]
        
        logger.info(f"Bulk indexed {processed} resumes with {total_chunks} total chunks")
        
        return UploadResponse(
            success=True,
            message=f"Successfully indexed {processed} resumes with {total_chunks} chunks",
            job_id=job_id,
            count=processed
        )
    
    except Exception as e:
        logger.error(f"Failed to bulk upload resumes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/jobs/{job_id}/candidates", tags=["Resumes"])
async def list_candidates(
    job_id: str,
    rag_processor: RAGProcessor = Depends(get_rag_processor)
):
    """List all candidates indexed for a job."""
    if job_id not in app_state.job_descriptions:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        # Get candidates from stored profiles if available, otherwise from RAG
        if job_id in app_state.candidate_profiles and app_state.candidate_profiles[job_id]:
            candidates = [
                {
                    "candidate_id": profile.candidate_id,
                    "candidate_name": profile.name,
                    "metadata": {}
                }
                for profile in app_state.candidate_profiles[job_id].values()
            ]
        else:
            # Fallback to RAG processor
            candidates = rag_processor.get_all_candidates_for_job(job_id)
        
        return {
            "job_id": job_id,
            "total_candidates": len(candidates),
            "candidates": candidates
        }
    
    except Exception as e:
        logger.error(f"Failed to list candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _match_skills(candidate_skills: List[str], job_skills: List[str]) -> Dict[str, Any]:
    """
    Match candidate skills with job description skills.
    
    Returns:
        Dictionary with matched_skills, missing_skills, and match_percentage
    """
    # Normalize skills (lowercase for comparison)
    candidate_skills_lower = [s.lower().strip() for s in candidate_skills]
    job_skills_lower = [s.lower().strip() for s in job_skills]
    
    matched = []
    missing = []
    
    for job_skill in job_skills:
        job_skill_lower = job_skill.lower().strip()
        # Check for exact match
        if job_skill_lower in candidate_skills_lower:
            matched.append(job_skill)
        else:
            # Check for partial match (skill contains keyword or vice versa)
            found = False
            for candidate_skill in candidate_skills:
                candidate_skill_lower = candidate_skill.lower().strip()
                if (job_skill_lower in candidate_skill_lower or 
                    candidate_skill_lower in job_skill_lower):
                    matched.append(job_skill)
                    found = True
                    break
            if not found:
                missing.append(job_skill)
    
    # Calculate match percentage
    match_percentage = (len(matched) / len(job_skills) * 100) if job_skills else 0.0
    
    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "match_percentage": round(match_percentage, 2)
    }


@app.get("/api/v1/jobs/{job_id}/candidates/{candidate_id}", response_model=CandidateDetailResponse, tags=["Resumes"])
async def get_candidate_detail(
    job_id: str,
    candidate_id: str
):
    """Get detailed information about a specific candidate."""
    if job_id not in app_state.job_descriptions:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get candidate profile
    if job_id not in app_state.candidate_profiles:
        raise HTTPException(status_code=404, detail="No candidates found for this job")
    
    if candidate_id not in app_state.candidate_profiles[job_id]:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    profile = app_state.candidate_profiles[job_id][candidate_id]
    jd = app_state.job_descriptions[job_id]
    
    # Match skills with job description
    job_skills = (jd.mandatory_skills or []) + (jd.optional_skills or [])
    skill_match = _match_skills(profile.skills, job_skills)
    
    # Build response
    response = CandidateDetailResponse(
        candidate_id=profile.candidate_id,
        name=profile.name,
        email=profile.email,
        phone=profile.phone,
        experience_years=profile.experience_years,
        experience_summary=profile.experience_summary,
        skills=profile.skills,
        education=profile.education,
        matched_skills=skill_match["matched_skills"],
        missing_skills=skill_match["missing_skills"],
        match_percentage=skill_match["match_percentage"]
    )
    
    return response


@app.post("/api/v1/compare", response_model=StrictComparisonResponse, tags=["Resumes"])
async def compare_candidates(
    request: CompareRequest,
    client_id: str = Depends(check_rate_limit)
):
    """Compare multiple candidates side-by-side with strict ranking."""
    job_id = request.job_id
    
    if job_id not in app_state.job_descriptions:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_id not in app_state.candidate_profiles:
        raise HTTPException(status_code=404, detail="No candidates found for this job")
    
    jd = app_state.job_descriptions[job_id]
    
    # Gather candidate data for LLM
    candidate_texts = []
    for cid in request.candidate_ids:
        if cid in app_state.candidate_profiles[job_id]:
            profile = app_state.candidate_profiles[job_id][cid]
            candidate_texts.append(f"CANDIDATE: {profile.name}\nRESUME:\n{profile.raw_text[:2000]}")
    
    if len(candidate_texts) < 2:
        raise HTTPException(status_code=400, detail="At least 2 valid candidates required for comparison")

    comparison_prompt = f"""
    Compare multiple candidates for the same job role.

    Return ONLY valid JSON. No explanations.

    JSON SCHEMA:
    {{
      "job_id": "{job_id}",
      "ranking": [
        {{
          "candidate_name": string,
          "match_score": number,
          "key_advantages": string[],
          "key_gaps": string[]
        }}
      ],
      "best_candidate": string
    }}

    RULES:
    - ranking must be sorted by match_score (highest first)
    - match_score must be 0-100
    - Do NOT repeat resume text
    - Use short bullet-style strings

    Job Description:
    {jd.description}

    Candidates:
    {"\n\n".join(candidate_texts)}
    """
    
    parser = ResumeParser()
    comp_response = parser.groq_client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": comparison_prompt}],
        temperature=0.1
    )
    comp_content = comp_response.choices[0].message.content.strip()
    if comp_content.startswith("```"):
        comp_content = re.sub(r'^```json?\n?', '', comp_content)
        comp_content = re.sub(r'\n?```$', '', comp_content)
    
    return json.loads(comp_content)



# ==================== PDF Extraction Endpoints ====================

@app.post("/api/v1/extract-pdf", tags=["PDF"])
async def extract_pdf_text(
    file: UploadFile = File(...),
    client_id: str = Depends(check_rate_limit)
):
    """
    Extract text from an uploaded PDF file.
    
    Accepts a single PDF file and returns the extracted text as JSON.
    This endpoint is useful for extracting resume text before processing.
    
    **File Requirements:**
    - Must be a valid PDF file (.pdf extension)
    - Content-Type: application/pdf
    - Maximum file size: Recommended under 10MB
    
    **Response:**
    - success: Boolean indicating success
    - filename: Original filename
    - file_size: File size in bytes
    - text: Extracted text content
    - text_length: Number of characters extracted
    - page_count: Number of pages processed
    """
    # Validate file extension
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files (.pdf) are accepted."
        )
    
    # Validate content type (optional, but warn if unexpected)
    if file.content_type and file.content_type != 'application/pdf':
        logger.warning(f"Unexpected content type for {file.filename}: {file.content_type}")
    
    try:
        # Read file content
        pdf_bytes = await file.read()
        
        if len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Check file size (optional: enforce a reasonable limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(pdf_bytes) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {max_size / (1024*1024):.0f}MB"
            )
        
        # Validate PDF structure
        if not PDFExtractor.validate_pdf(pdf_bytes):
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file. The file may be corrupted or not a valid PDF."
            )
        
        # Extract text
        extracted_text = PDFExtractor.extract_text(pdf_bytes)
        
        # Count pages (re-read to get page count)
        try:
            pdf_stream = BytesIO(pdf_bytes)
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_stream)
            page_count = len(reader.pages)
        except:
            page_count = 1  # Fallback if we can't count
        
        logger.info(
            f"Successfully extracted text from PDF: {file.filename} "
            f"({len(pdf_bytes)} bytes, {len(extracted_text)} chars, {page_count} pages)"
        )
        
        return {
            "success": True,
            "filename": file.filename,
            "file_size": len(pdf_bytes),
            "text": extracted_text,
            "text_length": len(extracted_text),
            "page_count": page_count,
            "message": "Text extracted successfully"
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"PDF extraction error for {file.filename}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during PDF extraction: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract text from PDF: {str(e)}"
        )


@app.post("/api/v1/analyze-resume", response_model=StrictEvaluationResponse, tags=["Resumes"])
async def analyze_resume(
    file: UploadFile = File(...),
    jd_text: str = Form(...),
    job_id: Optional[str] = Form(None),
    rag_processor: RAGProcessor = Depends(get_rag_processor),
    client_id: str = Depends(check_rate_limit)
):
    """
    One-shot resume analysis:
    1. Extract text from PDF
    2. Extract structured data using LLM
    3. Compare against JD
    4. Index for RAG
    5. Return exact JSON format required
    """
    # 1. Extract text from PDF
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    try:
        pdf_bytes = await file.read()
        if not PDFExtractor.validate_pdf(pdf_bytes):
            raise HTTPException(status_code=400, detail="Invalid PDF file")
        
        extracted_text = PDFExtractor.extract_text(pdf_bytes)
        
        # 2. Extract structured data using LLM
        parser = ResumeParser()
        parsed_data = parser.parse_with_llm(extracted_text)
        
        candidate_id = generate_candidate_id()
        candidate_name = parsed_data.get("candidate_name", file.filename.split('.')[0])
        
        # 3. Compare against JD
        # We need to extract skills from JD text if they aren't provided as a list
        # For simplicity, we'll ask the LLM to do the comparison if possible, 
        # but here we can just use the parser's logic if we have structured JD.
        # Actually, let's use the rag_processor's evaluate_with_llm but adapted.
        
        # 0. Set effective job ID
        effective_job_id = job_id or "default"

        # 3. Compare against JD

        # 3. Compare against JD
        evaluation_prompt = f"""
        Perform a professional ATS evaluation of the candidate resume against the job description.

        Return ONLY the JSON schema below and NOTHING else.

        JSON SCHEMA (STRICT):
        {{
          "candidate_name": "{candidate_name}",
          "job_id": "{effective_job_id}",
          "overall_match_score": number,
          "skills": {{
            "matched": string[],
            "missing": string[],
            "partial": string[]
          }},
          "experience": {{
            "required_years": number | null,
            "candidate_years": number | null,
            "match": string
          }},
          "education": {{
            "required": string | null,
            "candidate": string | null,
            "match": string
          }},
          "strengths": string[],
          "gaps": string[],
          "summary": string,
          "recommendation": "Strong Fit" | "Moderate Fit" | "Weak Fit"
        }}

        RULES:
        - overall_match_score must be between 0 and 100
        - Use concise, ATS-style language
        - Do NOT infer skills that are not explicitly present
        - Skills must be normalized (e.g., "React.js" -> "React")
        - Never add fields not listed in the schema

        Job Description:
        {jd_text}

        Candidate Resume:
        {extracted_text}
        """
        
        eval_response = parser.groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": evaluation_prompt}],
            temperature=0.1
        )
        eval_content = eval_response.choices[0].message.content.strip()
        if eval_content.startswith("```"):
            eval_content = re.sub(r'^```json?\n?', '', eval_content)
            eval_content = re.sub(r'\n?```$', '', eval_content)
        eval_data = json.loads(eval_content)
        eval_data["candidate_id"] = candidate_id

        # 4. Index for RAG
        rag_processor.index_resume(
            job_id=effective_job_id,
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            resume_text=extracted_text
        )
        
        # 5. Store in app state
        if effective_job_id not in app_state.candidate_profiles:
            app_state.candidate_profiles[effective_job_id] = {}
            
        profile = CandidateProfile(
            candidate_id=candidate_id,
            job_id=effective_job_id,
            name=candidate_name,
            email=parsed_data.get("email", ""),
            phone=parsed_data.get("phone", ""),
            skills=eval_data["skills"]["matched"],
            education=[eval_data["education"]["candidate"] or ""],
            experience_summary=eval_data["summary"],
            raw_text=extracted_text
        )
        app_state.candidate_profiles[effective_job_id][candidate_id] = profile

        # Return the strict evaluation data
        return eval_data

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



# ==================== Evaluation Endpoints ====================

@app.post("/api/v1/evaluate", response_model=EvaluationResponse, tags=["Evaluation"])
async def evaluate_candidates(
    request: EvaluationRequest,
    evaluator: CandidateEvaluator = Depends(get_evaluator),
    client_id: str = Depends(check_rate_limit)
):
    """
    Evaluate candidates against a job description.
    
    Returns ranked list of candidates with scores and recommendations.
    """
    job_id = request.job_id
    
    if job_id not in app_state.job_descriptions:
        raise HTTPException(status_code=404, detail="Job not found")
    
    jd = app_state.job_descriptions[job_id]
    
    try:
        # Check cache if no specific candidates requested
        cache_key = f"{job_id}_all" if not request.candidate_ids else f"{job_id}_{'_'.join(sorted(request.candidate_ids))}"
        
        if cache_key in app_state.evaluation_cache:
            logger.info(f"Returning cached evaluation for {job_id}")
            return app_state.evaluation_cache[cache_key]
        
        # Run evaluation
        logger.info(f"Starting evaluation for job: {job_id}")
        
        evaluations = evaluator.evaluate_candidates(
            jd=jd,
            candidate_ids=request.candidate_ids
        )
        
        # Infer role level
        role_level = evaluator.role_inferrer.infer_role_level(jd)
        
        # Build response
        response = EvaluationResponse(
            job_id=job_id,
            job_title=jd.title,
            role_level=role_level,
            total_candidates=len(evaluations),
            evaluation_timestamp=datetime.utcnow(),
            candidates=evaluations
        )
        
        # Cache the result
        app_state.evaluation_cache[cache_key] = response
        
        logger.info(f"Completed evaluation for {len(evaluations)} candidates")
        
        return response
    
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@app.get("/api/v1/jobs/{job_id}/evaluate", response_model=EvaluationResponse, tags=["Evaluation"])
async def evaluate_all_candidates(
    job_id: str,
    evaluator: CandidateEvaluator = Depends(get_evaluator),
    client_id: str = Depends(check_rate_limit)
):
    """Evaluate all candidates for a specific job."""
    request = EvaluationRequest(job_id=job_id)
    return await evaluate_candidates(request, evaluator, client_id)


@app.get(
    "/api/v1/jobs/{job_id}/candidates/{candidate_id}/evaluate",
    response_model=CandidateEvaluation,
    tags=["Evaluation"]
)
async def evaluate_single_candidate(
    job_id: str,
    candidate_id: str,
    evaluator: CandidateEvaluator = Depends(get_evaluator),
    client_id: str = Depends(check_rate_limit)
):
    """Evaluate a specific candidate for a job."""
    if job_id not in app_state.job_descriptions:
        raise HTTPException(status_code=404, detail="Job not found")
    
    jd = app_state.job_descriptions[job_id]
    
    try:
        evaluation = evaluator.evaluate_single(jd=jd, candidate_id=candidate_id)
        
        if not evaluation:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        return evaluation
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Single candidate evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Results Endpoints ====================

@app.get("/api/v1/results/{job_id}", response_model=EvaluationResponse, tags=["Results"])
async def get_cached_results(job_id: str):
    """Get cached evaluation results for a job."""
    cache_key = f"{job_id}_all"
    
    if cache_key not in app_state.evaluation_cache:
        raise HTTPException(
            status_code=404,
            detail="No cached results found. Run evaluation first."
        )
    
    return app_state.evaluation_cache[cache_key]


@app.get("/api/v1/results/{job_id}/top", tags=["Results"])
async def get_top_candidates(
    job_id: str,
    limit: int = Query(default=10, ge=1, le=50)
):
    """Get top N candidates from cached results."""
    cache_key = f"{job_id}_all"
    
    if cache_key not in app_state.evaluation_cache:
        raise HTTPException(
            status_code=404,
            detail="No cached results found. Run evaluation first."
        )
    
    cached = app_state.evaluation_cache[cache_key]
    top_candidates = cached.candidates[:limit]
    
    return {
        "job_id": job_id,
        "job_title": cached.job_title,
        "total_candidates": cached.total_candidates,
        "showing": len(top_candidates),
        "candidates": top_candidates
    }


@app.get("/api/v1/results/{job_id}/summary", tags=["Results"])
async def get_results_summary(job_id: str):
    """Get a summary of evaluation results."""
    cache_key = f"{job_id}_all"
    
    if cache_key not in app_state.evaluation_cache:
        raise HTTPException(
            status_code=404,
            detail="No cached results found. Run evaluation first."
        )
    
    cached = app_state.evaluation_cache[cache_key]
    
    # Calculate summary statistics
    strong_fit = sum(1 for c in cached.candidates if c.overall_recommendation.value == "Strong Fit")
    partial_fit = sum(1 for c in cached.candidates if c.overall_recommendation.value == "Partial Fit")
    weak_fit = sum(1 for c in cached.candidates if c.overall_recommendation.value == "Weak Fit")
    
    scores = [c.scores.final_score for c in cached.candidates]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    return {
        "job_id": job_id,
        "job_title": cached.job_title,
        "role_level": cached.role_level.value,
        "total_candidates": cached.total_candidates,
        "evaluation_timestamp": cached.evaluation_timestamp.isoformat(),
        "summary": {
            "strong_fit_count": strong_fit,
            "partial_fit_count": partial_fit,
            "weak_fit_count": weak_fit,
            "average_score": round(avg_score, 2),
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0
        }
    }


# ==================== Run Application ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 