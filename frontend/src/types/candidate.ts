export type RoleLevel = 'Intern' | 'Junior' | 'Mid' | 'Senior' | 'Lead';
export type Recommendation = 'Strong Fit' | 'Partial Fit' | 'Weak Fit';

export interface ScoreBreakdown {
  skills_score: number;
  experience_score: number;
  education_score: number;
  final_score: number;
}

export interface Candidate {
  id: string;
  name: string;
  roleLevel: RoleLevel;
  scores: ScoreBreakdown;
  matchedSkills: string[];
  missingSkills: string[];
  experienceSummary: string;
  strengths: string[];
  weaknesses: string[];
  confidenceNote: string;
  recommendation: Recommendation;
  education?: string;
}

export interface JobDescription {
  id?: string;
  title: string;
  description: string;
  mandatory_skills?: string[];
  optional_skills?: string[];
  min_experience_years?: number;
  education_requirements?: string;
}

// Backend JobDescription format (matches backend JobDescriptionInput schema)
export interface JobDescriptionBackend {
  job_id?: string;
  title: string;
  description: string;
  mandatory_skills?: string[];
  optional_skills?: string[];
  min_experience_years?: number;
  education_requirements?: string;
}

// Backend CandidateEvaluation format
export interface CandidateEvaluationBackend {
  candidate_id: string;
  candidate_name: string;
  role_level: RoleLevel;
  scores: ScoreBreakdown;
  matched_skills: string[];
  missing_skills: string[];
  relevant_experience: string;
  strengths: string[];
  weaknesses: string[];
  overall_recommendation: Recommendation;
  confidence_notes: string;
}

export interface EvaluationResponse {
  job_id: string;
  job_title: string;
  role_level: RoleLevel;
  total_candidates: number;
  evaluation_timestamp: string;
  candidates: CandidateEvaluationBackend[];
}

// Candidate Detail Response (from /api/v1/jobs/{job_id}/candidates/{candidate_id})
export interface CandidateDetailResponse {
  candidate_id: string;
  name: string;
  email: string;
  phone: string;
  experience_years: number;
  experience_summary: string;
  skills: string[];
  education: string[];
  matched_skills: string[];
  missing_skills: string[];
  match_percentage: number;
}

// Compare Response
export interface CompareResponse {
  job_id: string;
  candidates: CandidateDetailResponse[];
}

export interface AnalyzeResumeResponse {
  candidate_id: string;
  name: string;
  skills: string[];
  missing_skills: string[];
  experience: string;
  education: string;
  match_score: number;
}

export interface StrictEvaluationResponse {
  candidate_name: string;
  job_id: string;
  overall_match_score: number;
  skills: {
    matched: string[];
    missing: string[];
    partial: string[];
  };
  experience: {
    required_years: number | null;
    candidate_years: number | null;
    match: string;
  };
  education: {
    required: string | null;
    candidate: string | null;
    match: string;
  };
  strengths: string[];
  gaps: string[];
  summary: string;
  recommendation: 'Strong Fit' | 'Moderate Fit' | 'Weak Fit';
}

export interface StrictComparisonRankingItem {
  candidate_name: string;
  match_score: number;
  key_advantages: string[];
  key_gaps: string[];
}

export interface StrictComparisonResponse {
  job_id: string;
  ranking: StrictComparisonRankingItem[];
  best_candidate: string;
}
