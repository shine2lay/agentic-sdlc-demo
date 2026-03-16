import { memo } from 'react';

interface MetricCellProps {
  label: string;
  value: string;
  compact?: boolean;
}

export const MetricCell = memo(function MetricCell({ label, value, compact }: MetricCellProps) {
  return (
    <div className={`flex flex-col rounded-md bg-gray-800 ${compact ? 'px-2 py-1' : 'p-2'}`}>
      <span className="text-xs text-gray-500">{label}</span>
      <span className={`font-medium text-gray-200 ${compact ? 'text-xs' : 'text-sm'}`}>{value}</span>
    </div>
  );
});
