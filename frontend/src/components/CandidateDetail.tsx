import { User, CheckCircle2, XCircle, Lightbulb, AlertCircle } from 'lucide-react';
import { Candidate } from '@/types/candidate';
import { StatusBadge } from './StatusBadge';
import { ScoreBar } from './ScoreBar';
import { Badge } from '@/components/ui/badge';

interface CandidateDetailProps {
  candidate: Candidate;
}

export function CandidateDetail({ candidate }: CandidateDetailProps) {
  return (
    <div className="card-elevated animate-slide-in-right overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-border bg-gradient-to-r from-primary/5 to-transparent">
        <div className="flex items-start gap-4">
          <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
            <User className="w-7 h-7 text-primary" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-1">
              <h2 className="text-xl font-semibold text-foreground">{candidate.name}</h2>
              <StatusBadge status={candidate.recommendation} />
            </div>
            <p className="text-sm text-muted-foreground">{candidate.roleLevel} candidate</p>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-foreground">{Math.round(candidate.scores.final_score)}</div>
            <div className="text-xs text-muted-foreground font-medium">Match Score</div>
          </div>
        </div>
      </div>

      {/* Score Breakdown */}
      <div className="p-6 border-b border-border">
        <h3 className="text-sm font-semibold text-foreground mb-4">Score Breakdown</h3>
        <div className="space-y-4">
          <ScoreBar score={candidate.scores.skills_score} label="Skills Match" />
          <ScoreBar score={candidate.scores.experience_score} label="Experience Relevance" />
          <ScoreBar score={candidate.scores.education_score} label="Education Fit" />
        </div>
      </div>

      {/* Skills */}
      <div className="p-6 border-b border-border">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-success" />
              Matched Skills
            </h4>
            <div className="flex flex-wrap gap-2">
              {candidate.matchedSkills.map((skill) => (
                <Badge key={skill} className="bg-success/10 text-success border-success/20 hover:bg-success/20">
                  {skill}
                </Badge>
              ))}
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
              <XCircle className="w-4 h-4 text-destructive" />
              Missing Skills
            </h4>
            <div className="flex flex-wrap gap-2">
              {candidate.missingSkills.length > 0 ? (
                candidate.missingSkills.map((skill) => (
                  <Badge key={skill} variant="outline" className="border-destructive/30 text-destructive">
                    {skill}
                  </Badge>
                ))
              ) : (
                <span className="text-sm text-muted-foreground">All required skills matched</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Evaluation Summary */}
      <div className="p-6 border-b border-border">
        <h3 className="text-sm font-semibold text-foreground mb-3">Evaluation Summary</h3>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {candidate.experienceSummary}
        </p>
      </div>

      {/* Education */}
      {candidate.education && (
        <div className="p-6 border-b border-border">
          <h3 className="text-sm font-semibold text-foreground mb-3">Education</h3>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {candidate.education}
          </p>
        </div>
      )}

      {/* Strengths & Weaknesses */}
      <div className="p-6 border-b border-border">
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-success" />
              Strengths
            </h4>
            <ul className="space-y-2">
              {candidate.strengths.map((strength, index) => (
                <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-success mt-1.5 flex-shrink-0" />
                  {strength}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-warning" />
              Key Gaps
            </h4>
            <ul className="space-y-2">
              {candidate.weaknesses.map((weakness, index) => (
                <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-warning mt-1.5 flex-shrink-0" />
                  {weakness}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Confidence Note */}
      <div className="p-6 bg-muted/30">
        <h3 className="text-sm font-semibold text-foreground mb-2">Assessment Confidence</h3>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {candidate.confidenceNote}
        </p>
      </div>
    </div>
  );
}
