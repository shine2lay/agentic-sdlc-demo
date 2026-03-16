import { useState } from 'react';
import { cn } from '../../utils';

interface CollapsibleSectionProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

export function CollapsibleSection({ title, children, defaultOpen = false }: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-800 rounded-md transition-colors"
      >
        <span
          className={cn(
            'inline-block transition-transform text-gray-500 text-xs',
            open && 'rotate-90',
          )}
          aria-hidden="true"
        >
          &#9654;
        </span>
        {title}
      </button>
      {open && (
        <div className="px-3 pb-2">
          {children}
        </div>
      )}
    </div>
  );
}
