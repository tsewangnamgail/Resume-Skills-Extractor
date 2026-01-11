import { cn } from '@/lib/utils';

interface ScoreBarProps {
  score: number;
  label: string;
  showValue?: boolean;
  size?: 'sm' | 'md';
  className?: string;
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'bg-success';
  if (score >= 60) return 'bg-warning';
  return 'bg-destructive';
}

export function ScoreBar({ score, label, showValue = true, size = 'md', className }: ScoreBarProps) {
  return (
    <div className={cn('space-y-1.5', className)}>
      <div className="flex items-center justify-between">
        <span className={cn(
          'font-medium text-foreground',
          size === 'sm' ? 'text-xs' : 'text-sm'
        )}>
          {label}
        </span>
        {showValue && (
          <span className={cn(
            'font-semibold text-foreground',
            size === 'sm' ? 'text-xs' : 'text-sm'
          )}>
            {score}%
          </span>
        )}
      </div>
      <div className={cn('score-bar', size === 'sm' ? 'h-1.5' : 'h-2')}>
        <div
          className={cn('score-bar-fill', getScoreColor(score))}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
