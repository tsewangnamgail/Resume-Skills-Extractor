import { Candidate, JobDescription, JobDescriptionBackend, EvaluationResponse, CandidateEvaluationBackend, CandidateDetailResponse, CompareResponse, AnalyzeResumeResponse, StrictEvaluationResponse, StrictComparisonResponse } from '../types/candidate';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiService = {
    /**
     * Create a new job description
     */
    async createJob(jd: JobDescription): Promise<any> {
        const response = await fetch(`${API_BASE_URL}/api/v1/jobs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(jd),
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ message: 'Failed to create job' }));
            throw new Error(error.message || 'Failed to create job');
        }
        return response.json();
    },

    /**
     * Update an existing job description
     */
    async updateJob(jobId: string, jd: JobDescription): Promise<any> {
        const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ...jd, job_id: jobId }),
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ message: 'Failed to update job' }));
            throw new Error(error.message || 'Failed to update job');
        }
        return response.json();
    },

    /**
     * Get a job description by ID
     */
    async getJob(jobId: string): Promise<JobDescriptionBackend> {
        const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}`);
        if (!response.ok) throw new Error('Failed to fetch job');
        return response.json();
    },

    /**
     * Upload multiple resumes for a job
     */
    async uploadResumes(jobId: string, resumes: { candidate_id: string, candidate_name: string, resume_text: string, metadata?: any }[]): Promise<any> {
        const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}/resumes/bulk`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_id: jobId, resumes }),
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ message: 'Failed to upload resumes' }));
            throw new Error(error.message || 'Failed to upload resumes');
        }
        return response.json();
    },

    /**
     * Evaluate all candidates for a job
     */
    async evaluateCandidates(jobId: string): Promise<EvaluationResponse> {
        const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}/evaluate`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ message: 'Failed to start evaluation' }));
            throw new Error(error.message || 'Failed to start evaluation');
        }
        return response.json();
    },

    /**
     * Get candidates for a job (returns raw candidate list, not evaluated)
     */
    async getCandidates(jobId: string): Promise<any[]> {
        const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}/candidates`);
        if (!response.ok) throw new Error('Failed to fetch candidates');
        const data = await response.json();
        return data.candidates || [];
    },

    /**
     * Get detailed information about a specific candidate
     */
    async getCandidateDetail(jobId: string, candidateId: string): Promise<CandidateDetailResponse> {
        const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}/candidates/${candidateId}`);
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Failed to fetch candidate details' }));
            throw new Error(error.detail || error.message || 'Failed to fetch candidate details');
        }
        return response.json();
    },

    /**
     * Compare multiple candidates
     */
    async compareCandidates(jobId: string, candidateIds: string[]): Promise<StrictComparisonResponse> {
        const response = await fetch(`${API_BASE_URL}/api/v1/compare`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_id: jobId, candidate_ids: candidateIds }),
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Failed to compare candidates' }));
            throw new Error(error.detail || error.message || 'Failed to compare candidates');
        }
        return response.json();
    },

    /**
     * One-shot resume analysis (PFD extract + Parse + Compare)
     */
    async analyzeResume(file: File, jdText: string, jobId?: string): Promise<StrictEvaluationResponse> {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('jd_text', jdText);
        if (jobId) formData.append('job_id', jobId);

        const response = await fetch(`${API_BASE_URL}/api/v1/analyze-resume`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ message: 'Failed to analyze resume' }));
            throw new Error(error.message || 'Failed to analyze resume');
        }
        return response.json();
    },

    /**
     * Health check
     */
    async healthCheck(): Promise<boolean> {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            return response.ok;
        } catch {
            return false;
        }
    }
};
