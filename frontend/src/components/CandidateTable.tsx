import { User, ChevronRight, Trophy } from 'lucide-react';
import { Candidate } from '@/types/candidate';
import { StatusBadge } from './StatusBadge';
import { cn } from '@/lib/utils';

interface CandidateTableProps {
  candidates: Candidate[];
  selectedId: string | null;
  onSelect: (candidate: Candidate) => void;
}

export function CandidateTable({ candidates, selectedId, onSelect }: CandidateTableProps) {
  const sortedCandidates = [...candidates].sort((a, b) => b.finalScore - a.finalScore);

  return (
    <div className="card-elevated overflow-hidden animate-fade-in" style={{ animationDelay: '0.1s' }}>
      <div className="p-4 border-b border-border">
        <h3 className="text-lg font-semibold text-foreground">Ranked Candidates</h3>
        <p className="text-sm text-muted-foreground mt-1">
          {candidates.length} candidates evaluated
        </p>
      </div>
      <div className="divide-y divide-border">
        {sortedCandidates.map((candidate, index) => (
          <button
            key={candidate.id}
            onClick={() => onSelect(candidate)}
            className={cn(
              'w-full p-4 flex items-center gap-4 text-left transition-colors hover:bg-muted/50',
              selectedId === candidate.id && 'bg-primary/5 hover:bg-primary/5'
            )}
          >
            <div className="relative flex-shrink-0">
              <div className={cn(
                'w-10 h-10 rounded-full flex items-center justify-center',
                index < 3 ? 'bg-primary/10' : 'bg-muted'
              )}>
                <User className={cn(
                  'w-5 h-5',
                  index < 3 ? 'text-primary' : 'text-muted-foreground'
                )} />
              </div>
              {index < 3 && (
                <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-accent flex items-center justify-center">
                  <Trophy className="w-3 h-3 text-accent-foreground" />
                </div>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-medium text-foreground truncate">
                  {candidate.name}
                </span>
                <StatusBadge status={candidate.recommendation} />
              </div>
              <span className="text-sm text-muted-foreground">{candidate.email}</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-2xl font-bold text-foreground">{candidate.finalScore}</div>
                <div className="text-xs text-muted-foreground">Score</div>
              </div>
              <ChevronRight className={cn(
                'w-5 h-5 text-muted-foreground transition-colors',
                selectedId === candidate.id && 'text-primary'
              )} />
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
