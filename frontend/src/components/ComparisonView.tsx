import { ArrowLeftRight, CheckCircle2, XCircle, Crown, Loader2 } from 'lucide-react';
import { Candidate, StrictComparisonResponse } from '@/types/candidate';
import { ScoreBar } from './ScoreBar';
import { Checkbox } from '@/components/ui/checkbox';
import { cn } from '@/lib/utils';
import { useEffect, useState } from 'react';
import { apiService } from '@/services/api';
import { toast } from 'sonner';

interface ComparisonViewProps {
  candidates: Candidate[];
  selectedIds: string[];
  onToggleCandidate: (id: string) => void;
  jobId?: string;
}

export function ComparisonView({ candidates, selectedIds, onToggleCandidate, jobId }: ComparisonViewProps) {
  const [comparisonData, setComparisonData] = useState<StrictComparisonResponse | null>(null);
  const [isComparing, setIsComparing] = useState(false);

  const selectedCandidates = candidates.filter(c => selectedIds.includes(c.id));
  const sortedCandidates = [...candidates].sort((a, b) => b.scores.final_score - a.scores.final_score);

  useEffect(() => {
    const fetchComparison = async () => {
      if (selectedIds.length < 2 || !jobId) {
        setComparisonData(null);
        return;
      }

      setIsComparing(true);
      try {
        const result = await apiService.compareCandidates(jobId, selectedIds);
        setComparisonData(result);
      } catch (error) {
        console.error('Comparison failed:', error);
        toast.error('Failed to generate AI comparison');
      } finally {
        setIsComparing(false);
      }
    };

    fetchComparison();
  }, [selectedIds, jobId]);

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {/* Candidate Selection Panel */}
      <div className="card-elevated overflow-hidden animate-fade-in">
        <div className="p-4 border-b border-border">
          <h3 className="text-lg font-semibold text-foreground">Select Candidates</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Choose candidates to compare
          </p>
        </div>
        <div className="divide-y divide-border">
          {sortedCandidates.map((candidate, index) => (
            <label
              key={candidate.id}
              className="flex items-center gap-3 p-4 hover:bg-muted/30 transition-colors cursor-pointer"
            >
              <Checkbox
                checked={selectedIds.includes(candidate.id)}
                onCheckedChange={() => onToggleCandidate(candidate.id)}
                aria-label={`Compare ${candidate.name}`}
              />
              <div className="flex items-center justify-center w-6 h-6 rounded-full bg-muted text-xs font-semibold text-muted-foreground">
                {index + 1}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-foreground truncate">{candidate.name}</div>
                <div className="text-xs text-muted-foreground">Score: {Math.round(candidate.scores.final_score)}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Comparison Results */}
      <div className="lg:col-span-2">
        {selectedCandidates.length < 2 ? (
          <div className="card-elevated p-8 text-center animate-fade-in h-full flex flex-col items-center justify-center">
            <ArrowLeftRight className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">Compare Candidates</h3>
            <p className="text-sm text-muted-foreground">
              Select at least 2 candidates to compare their qualifications side-by-side.
            </p>
          </div>
        ) : isComparing ? (
          <div className="card-elevated p-8 text-center animate-fade-in h-full flex flex-col items-center justify-center">
            <Loader2 className="w-12 h-12 text-primary animate-spin mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-foreground">Generating AI Comparison...</h3>
          </div>
        ) : (
          <ComparisonResults
            selectedCandidates={selectedCandidates}
            aiData={comparisonData}
          />
        )}
      </div>
    </div>
  );
}

function ComparisonResults({ selectedCandidates, aiData }: { selectedCandidates: Candidate[], aiData: StrictComparisonResponse | null }) {
  const bestCandidate = selectedCandidates.reduce((best, current) =>
    current.scores.final_score > best.scores.final_score ? current : best
  );

  const allSkills = new Set<string>();
  selectedCandidates.forEach(c => {
    c.matchedSkills.forEach(s => allSkills.add(s));
    c.missingSkills.forEach(s => allSkills.add(s));
  });

  return (
    <div className="card-elevated overflow-hidden animate-fade-in">
      <div className="p-4 border-b border-border">
        <h3 className="text-lg font-semibold text-foreground">AI Candidate Comparison</h3>
        <p className="text-sm text-muted-foreground mt-1">
          {aiData ? `AI recommends ${aiData.best_candidate}` : 'Side-by-side comparison'}
        </p>
      </div>

      {/* Comparison Advantage/Gaps */}
      {aiData && (
        <div className="p-6 border-b border-border bg-primary/5">
          <h4 className="text-sm font-semibold text-foreground mb-4">AI Ranking & Insights</h4>
          <div className="grid gap-6 md:grid-cols-2">
            {aiData.ranking.map((item, idx) => (
              <div key={idx} className="p-4 rounded-lg bg-card border border-border space-y-3">
                <div className="flex items-center justify-between">
                  <div className="font-bold text-foreground flex items-center gap-2">
                    {idx === 0 && <Crown className="w-4 h-4 text-warning" />}
                    {item.candidate_name}
                  </div>
                  <div className="text-xs font-semibold px-2 py-0.5 rounded bg-primary/10 text-primary">
                    {item.match_score}% Match
                  </div>
                </div>
                <div>
                  <div className="text-[10px] font-bold text-success uppercase mb-1">Key Advantages</div>
                  <ul className="text-xs text-muted-foreground space-y-1">
                    {item.key_advantages.map((adv, i) => (
                      <li key={i} className="flex items-start gap-1">
                        <span className="text-success mt-0.5">•</span>
                        {adv}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <div className="text-[10px] font-bold text-destructive uppercase mb-1">Key Gaps</div>
                  <ul className="text-xs text-muted-foreground space-y-1">
                    {item.key_gaps.map((gap, i) => (
                      <li key={i} className="flex items-start gap-1">
                        <span className="text-destructive mt-0.5">•</span>
                        {gap}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Score Comparison */}
      <div className="p-6 border-b border-border">
        <h4 className="text-sm font-semibold text-foreground mb-4">Score Comparison</h4>
        <div className="grid gap-6" style={{ gridTemplateColumns: `repeat(${selectedCandidates.length}, 1fr)` }}>
          {selectedCandidates.map((candidate) => (
            <div key={candidate.id} className="text-center">
              <div className={cn(
                'relative inline-flex flex-col items-center p-4 rounded-lg',
                candidate.id === bestCandidate.id ? 'bg-primary/5 ring-2 ring-primary/20' : 'bg-muted/30'
              )}>
                {candidate.id === bestCandidate.id && (
                  <Crown className="w-5 h-5 text-warning absolute -top-2 left-1/2 -translate-x-1/2" />
                )}
                <div className="text-3xl font-bold text-foreground">{Math.round(candidate.scores.final_score)}</div>
                <div className="text-sm font-medium text-foreground mt-1">{candidate.name}</div>
              </div>
              <div className="mt-4 space-y-3">
                <ScoreBar score={candidate.scores.skills_score} label="Skills" size="sm" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Skills Comparison */}
      <div className="p-6 border-b border-border">
        <h4 className="text-sm font-semibold text-foreground mb-4">Skills Comparison</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-2 pr-4 font-medium text-muted-foreground">Skill</th>
                {selectedCandidates.map((candidate) => (
                  <th key={candidate.id} className="text-center py-2 px-2 font-medium text-foreground">
                    {candidate.name.split(' ')[0]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from(allSkills).sort().map((skill) => (
                <tr key={skill} className="border-b border-border/50">
                  <td className="py-2 pr-4 text-foreground">{skill}</td>
                  {selectedCandidates.map((candidate) => (
                    <td key={candidate.id} className="text-center py-2 px-2">
                      {candidate.matchedSkills.includes(skill) ? (
                        <CheckCircle2 className="w-5 h-5 text-success mx-auto" />
                      ) : candidate.missingSkills.includes(skill) ? (
                        <XCircle className="w-5 h-5 text-destructive mx-auto" />
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recommendation */}
      <div className="p-6 bg-muted/30">
        <h4 className="text-sm font-semibold text-foreground mb-3">Recommendation</h4>
        <div className="flex items-start gap-3 p-4 rounded-lg bg-card border border-border">
          <Crown className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-foreground font-medium mb-1">
              {aiData?.best_candidate || bestCandidate.name} is recommended
            </p>
            <p className="text-sm text-muted-foreground">
              Based on the AI evaluation, this candidate demonstrates the best alignment with core requirements.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}