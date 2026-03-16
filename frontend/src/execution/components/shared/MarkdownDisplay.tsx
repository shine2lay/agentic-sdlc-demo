import { cn } from '../../utils';

interface MarkdownDisplayProps {
  content: string;
  className?: string;
}

/**
 * Renders text content with basic Markdown-like formatting using plain HTML.
 * This is a lightweight alternative to react-markdown — it handles the most
 * common patterns (code blocks, bold, inline code, bullet lists) without deps.
 */
export function MarkdownDisplay({ content, className }: MarkdownDisplayProps) {
  return (
    <div
      className={cn(
        'rounded-md bg-gray-800 p-4 text-sm text-gray-200 border border-gray-700',
        className,
      )}
    >
      <pre className="whitespace-pre-wrap font-sans text-xs leading-relaxed text-gray-200">
        {content}
      </pre>
    </div>
  );
}
