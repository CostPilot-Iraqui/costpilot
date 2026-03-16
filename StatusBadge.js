import { cn } from '../../lib/utils';
import { translateStatus } from '../../lib/utils';

const statusStyles = {
  draft: 'bg-slate-100 text-slate-700',
  pending: 'bg-amber-100 text-amber-700',
  validated: 'bg-emerald-100 text-emerald-700',
  rejected: 'bg-red-100 text-red-700',
  green: 'bg-emerald-100 text-emerald-700',
  orange: 'bg-amber-100 text-amber-700',
  red: 'bg-red-100 text-red-700',
};

export function StatusBadge({ status, className }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        statusStyles[status] || statusStyles.draft,
        className
      )}
      data-testid={`status-badge-${status}`}
    >
      {translateStatus(status)}
    </span>
  );
}

export function VarianceIndicator({ value, className }) {
  const status = value <= 0 ? 'green' : value <= 5 ? 'orange' : 'red';
  const label = value <= 0 ? 'Contrôlé' : value <= 5 ? 'À surveiller' : 'Critique';

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
        statusStyles[status],
        className
      )}
      data-testid={`variance-indicator-${status}`}
    >
      <span className={cn(
        'h-1.5 w-1.5 rounded-full',
        status === 'green' ? 'bg-emerald-500' : status === 'orange' ? 'bg-amber-500' : 'bg-red-500'
      )} />
      {label}
    </span>
  );
}
