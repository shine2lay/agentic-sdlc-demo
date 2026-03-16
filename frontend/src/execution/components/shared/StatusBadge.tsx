import { memo } from 'react';
import { cn } from '../../utils';
import { STATUS_ICONS } from '../../constants';

const STATUS_STYLES: Record<string, string> = {
  completed: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  running: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  failed: 'bg-red-500/20 text-red-400 border-red-500/30',
  pending: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
};

export const StatusBadge = memo(function StatusBadge({
  status,
  className,
}: {
  status: string;
  className?: string;
}) {
  const icon = STATUS_ICONS[status] ?? '';
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-xs border font-medium',
        STATUS_STYLES[status] ?? STATUS_STYLES.pending,
        className,
      )}
    >
      {icon && <span className="mr-1">{icon}</span>}
      {status}
    </span>
  );
});
