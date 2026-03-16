import { cn } from '../../lib/utils';
import { Button } from '../ui/button';

export function EmptyState({ 
  icon: Icon, 
  title, 
  description, 
  action, 
  actionLabel, 
  imageUrl,
  className 
}) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 text-center', className)} data-testid="empty-state">
      {imageUrl ? (
        <div className="mb-6 h-48 w-full max-w-md overflow-hidden rounded-lg">
          <img 
            src={imageUrl} 
            alt="" 
            className="h-full w-full object-cover opacity-60"
          />
        </div>
      ) : Icon ? (
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-slate-100">
          <Icon className="h-8 w-8 text-slate-400" />
        </div>
      ) : null}
      <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
      {description && (
        <p className="mt-2 max-w-sm text-sm text-slate-500">{description}</p>
      )}
      {action && actionLabel && (
        <Button onClick={action} className="mt-6" data-testid="empty-state-action">
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
