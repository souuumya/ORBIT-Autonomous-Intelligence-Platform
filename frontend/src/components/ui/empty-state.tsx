import React from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  actionText,
  onAction,
  icon,
}) => {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-zinc-800 bg-zinc-950/40 p-8 text-center">
      <div className="mb-3 rounded-full bg-zinc-900/80 p-3 text-zinc-400 border border-zinc-800">
        {icon || <Inbox className="h-6 w-6 text-zinc-400" />}
      </div>
      <h4 className="mb-1 text-sm font-semibold text-zinc-200">{title}</h4>
      <p className="max-w-md text-xs text-zinc-400 mb-4">{description}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="rounded-md border border-cyan-500/30 bg-cyan-500/10 px-3.5 py-1.5 text-xs font-medium text-cyan-300 hover:bg-cyan-500/20 transition-all"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
