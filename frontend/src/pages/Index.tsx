import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Header } from '@/components/Header';
import { JobDescriptionCard } from '@/components/JobDescriptionCard';
import { JobDescriptionEditor } from '@/components/JobDescriptionEditor';
import { CandidateDetail } from '@/components/CandidateDetail';
import { ComparisonView } from '@/components/ComparisonView';
import { WelcomePage } from '@/components/WelcomePage';
import { ResumeUpload } from '@/components/ResumeUpload';
import { mockJobDescription } from '@/data/mockData';
import { Candidate, JobDescription, JobDescriptionBackend, Recommendation, RoleLevel } from '@/types/candidate';
import { Users, GitCompare, Play, Loader2 } from 'lucide-react';
import { apiService } from '@/services/api';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

const STORAGE_KEY = 'resumescreen_started_session';
const JOB_ID_KEY = 'resumescreen_job_id';

const Index = () => {
  const [hasStarted, setHasStarted] = useState<boolean>(() => {
    return sessionStorage.getItem(STORAGE_KEY) === 'true';
  });
  

  const [jobId, setJobId] = useState<string | null>(() => {
    const storedId = localStorage.getItem(JOB_ID_KEY);
    return storedId ? storedId : null;
  });

  const [jobDescription, setJobDescription] = useState<JobDescription>(mockJobDescription);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState('results');

  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);

  // Fetch job description safely
  const fetchJobDescription = async () => {
    if (!jobId) return;
    try {
      const job: JobDescriptionBackend = await apiService.getJob(jobId.toString());
      setJobDescription({
        id: job.job_id?.toString() || jobId.toString(),
        title: job.title,
        description: job.description,
        mandatory_skills: job.mandatory_skills || [],
        optional_skills: job.optional_skills || [],
        min_experience_years: job.min_experience_years,
        education_requirements: job.education_requirements,
      });
    } catch (error) {
      console.error('Failed to fetch job description:', error);
    }
  };

  // Fetch candidates safely
  const fetchCandidates = async () => {
    if (!jobId) return;
    setIsLoading(true);
    try {
      const rawCandidates = await apiService.getCandidates(jobId.toString());
      if (rawCandidates.length === 0) {
        setCandidates([]);
        return;
      }

      // Convert raw candidates to Candidate format (with placeholder data for non-evaluated)
      const mappedCandidates: Candidate[] = rawCandidates.map((c: any) => ({
        id: c.candidate_id,
        name: c.candidate_name || 'Unknown',
        roleLevel: 'Mid', // Default until evaluated
        scores: {
          skills_score: 0,
          experience_score: 0,
          education_score: 0,
          final_score: 0,
        },
        matchedSkills: [],
        missingSkills: [],
        experienceSummary: '',
        strengths: [],
        weaknesses: [],
        confidenceNote: '',
        recommendation: 'Partial Fit' as Recommendation,
      }));
      setCandidates(mappedCandidates);
    } catch (error) {
      console.error('Failed to fetch candidates:', error);
      setCandidates([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStart = () => {
    sessionStorage.setItem(STORAGE_KEY, 'true');
    setHasStarted(true);
  };
  

  const handleJobDescriptionSave = async (updatedJob: JobDescription) => {
    setIsLoading(true);
    try {
      if (jobId) {
        // Update existing job
        await apiService.updateJob(jobId.toString(), updatedJob);
        setJobDescription({ ...updatedJob, id: jobId });
        toast.success('Job description updated');
      } else {
        // Create new job
        const result = await apiService.createJob(updatedJob);
        const newJobId = result.job_id.toString();
        setJobId(newJobId);
        localStorage.setItem(JOB_ID_KEY, newJobId);
        setJobDescription({ ...updatedJob, id: newJobId });
        toast.success('Job description saved');
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to save job description');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyzeResults = (results: any[]) => {
    const mappedCandidates: Candidate[] = results.map((c) => ({
      id: c.candidate_id,
      name: c.candidate_name,
      roleLevel: 'Mid' as RoleLevel, // Default or derived from years
      scores: {
        skills_score: c.overall_match_score,
        experience_score: c.experience?.candidate_years ? (c.experience.candidate_years / (c.experience.required_years || 1)) * 100 : 0,
        education_score: c.education?.match === 'Match' ? 100 : c.education?.match === 'Partial' ? 50 : 0,
        final_score: c.overall_match_score,
      },
      matchedSkills: c.skills?.matched || [],
      missingSkills: [
        ...(c.skills?.missing || []),
        ...(c.skills?.partial || [])
      ],
      experienceSummary: c.summary || c.experience?.match || '',
      strengths: c.strengths || [],
      weaknesses: c.gaps || [],
      confidenceNote: `Education: ${c.education?.match}, Experience: ${c.experience?.match}`,
      recommendation: c.recommendation as Recommendation,
      education: c.education?.candidate || '',
    }));

    setCandidates((prev) => {
      const existingIds = new Set(prev.map(cand => cand.id));
      const newCandidates = mappedCandidates.filter(cand => !existingIds.has(cand.id));
      return [...prev, ...newCandidates].sort((a, b) => b.scores.final_score - a.scores.final_score);
    });
  };


  const handleCandidateSelect = async (candidate: Candidate) => {
    if (!jobId) return;

    // Set candidate immediately for UI responsiveness
    setSelectedCandidate(candidate);

    // Fetch full candidate details from backend
    try {
      const detail = await apiService.getCandidateDetail(jobId.toString(), candidate.id);

      // Convert detail to Candidate format
      // If candidate was already evaluated, keep the evaluation data
      // Otherwise, use the detail data
      const updatedCandidate: Candidate = {
        id: detail.candidate_id,
        name: detail.name,
        roleLevel: candidate.roleLevel, // Keep from evaluation if available
        scores: candidate.scores.final_score > 0 ? candidate.scores : {
          skills_score: detail.match_percentage,
          experience_score: 0,
          education_score: 0,
          final_score: detail.match_percentage,
        },
        matchedSkills: detail.matched_skills.length > 0 ? detail.matched_skills : candidate.matchedSkills,
        missingSkills: detail.missing_skills.length > 0 ? detail.missing_skills : candidate.missingSkills,
        experienceSummary: detail.experience_summary || candidate.experienceSummary,
        strengths: candidate.strengths,
        weaknesses: candidate.weaknesses,
        confidenceNote: candidate.confidenceNote,
        recommendation: candidate.recommendation,
      };

      setSelectedCandidate(updatedCandidate);

      // Update the candidate in the list as well
      setCandidates(prev =>
        prev.map(c => c.id === candidate.id ? updatedCandidate : c)
      );
    } catch (error) {
      console.error('Failed to fetch candidate details:', error);
      // Keep the existing candidate data if fetch fails
    }
  };

  const handleCompareToggle = (candidateId: string) => {
    setCompareIds((prev) =>
      prev.includes(candidateId)
        ? prev.filter((id) => id !== candidateId)
        : [...prev, candidateId]
    );
  };

  if (!hasStarted) return <WelcomePage onStart={handleStart} />;

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 py-8">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Left Column: Job & Upload */}
          <div className="lg:col-span-1 space-y-8">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Job Description</h3>
                <JobDescriptionEditor job={jobDescription} onSave={handleJobDescriptionSave} />
              </div>
              <JobDescriptionCard job={jobDescription} />
            </div>

            <ResumeUpload
              onAnalyzeResults={handleAnalyzeResults}
              jdText={jobDescription.description}
              jobId={jobId?.toString()}
            />

            
          </div>

          {/* Right Column: Results */}
          <div className="lg:col-span-2">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
              <div className="flex items-center justify-between">
                <TabsList className="bg-muted/50 p-1">
                  <TabsTrigger value="results" className="gap-2 data-[state=active]:bg-card">
                    <Users className="w-4 h-4" />
                    Candidates ({candidates.length})
                  </TabsTrigger>
                  <TabsTrigger value="compare" className="gap-2 data-[state=active]:bg-card">
                    <GitCompare className="w-4 h-4" />
                    Compare ({compareIds.length})
                  </TabsTrigger>
                </TabsList>

                {isLoading && <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />}
              </div>

              <TabsContent value="results" className="mt-0">
                <div className="grid gap-6">
                  {candidates.length === 0 ? (
                    <div className="card-elevated p-12 text-center">
                      <Users className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-foreground mb-2">No Candidates Yet</h3>
                      <p className="text-sm text-muted-foreground">
                        Upload some resumes to see them here and start the evaluation.
                      </p>
                    </div>
                  ) : (
                    <div className="grid gap-6 lg:grid-cols-2">
                      <div className="space-y-4">
                        <div className="card-elevated divide-y divide-border overflow-hidden">
                          {[...candidates]
                            .sort((a, b) => b.scores.final_score - a.scores.final_score)
                            .map((candidate, index) => (
                              <button
                                key={candidate.id}
                                onClick={() => handleCandidateSelect(candidate)}
                                className="w-full flex items-center gap-3 p-4 hover:bg-muted/30 transition-colors text-left"
                              >
                                <CandidateRow
                                  candidate={candidate}
                                  rank={index + 1}
                                  isSelected={selectedCandidate?.id === candidate.id}
                                />
                              </button>
                            ))}
                        </div>
                      </div>

                      <div className="lg:sticky lg:top-24 lg:self-start">
                        {selectedCandidate ? (
                          <CandidateDetail candidate={selectedCandidate} />
                        ) : (
                          <div className="card-elevated p-12 text-center">
                            <Users className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                            <h3 className="text-lg font-semibold text-foreground mb-2">Select a Candidate</h3>
                            <p className="text-sm text-muted-foreground">Click a candidate to view their analysis.</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="compare" className="mt-0">
                <ComparisonView
                  candidates={candidates}
                  selectedIds={compareIds}
                  onToggleCandidate={handleCompareToggle}
                  jobId={jobId?.toString()}
                />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </main>
    </div>
  );
};

// Candidate Row Component
interface CandidateRowProps {
  candidate: Candidate;
  rank: number;
  isSelected: boolean;
}

function CandidateRow({ candidate, rank, isSelected }: CandidateRowProps) {
  // Show skills or placeholder
  const skillsDisplay = candidate.matchedSkills.length > 0
    ? candidate.matchedSkills.slice(0, 3).join(', ') + (candidate.matchedSkills.length > 3 ? ` +${candidate.matchedSkills.length - 3} more` : '')
    : candidate.scores.final_score === 0 ? 'Not evaluated yet' : 'No skills matched';

  return (
    <div className={`flex items-center gap-4 py-1 rounded-lg transition-colors ${isSelected ? 'text-primary' : ''}`}>
      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-muted text-sm font-semibold text-muted-foreground">
        {rank}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-foreground">{candidate.name}</span>
          {candidate.scores.final_score > 0 && (
            <span
              className={`status-badge ${candidate.recommendation === 'Strong Fit'
                ? 'status-strong'
                : candidate.recommendation === 'Partial Fit'
                  ? 'status-partial'
                  : 'status-weak'
                }`}
            >
              {candidate.recommendation}
            </span>
          )}
        </div>
        <div className="text-sm text-muted-foreground truncate">
          {skillsDisplay}
        </div>
      </div>
      <div className="text-right">
        <div className="text-2xl font-bold text-foreground">
          {candidate.scores.final_score > 0 ? Math.round(candidate.scores.final_score) : '-'}
        </div>
      </div>
    </div>
  );
}

export default Index;
