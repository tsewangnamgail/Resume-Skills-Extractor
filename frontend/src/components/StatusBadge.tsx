import { cn } from '@/lib/utils';

import { Recommendation } from '@/types/candidate';

interface StatusBadgeProps {
  status: Recommendation;
  className?: string;
}

const statusConfig: Record<Recommendation, { label: string, className: string }> = {
  'Strong Fit': {
    label: 'Strong Fit',
    className: 'status-strong',
  },
  'Partial Fit': {
    label: 'Partial Fit',
    className: 'status-partial',
  },
  'Weak Fit': {
    label: 'Weak Fit',
    className: 'status-weak',
  },
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status] || statusConfig['Weak Fit'];

  return (
    <span className={cn('status-badge', config.className, className)}>
      {config.label}
    </span>
  );
}
