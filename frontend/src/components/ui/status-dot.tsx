import React from 'react';

export type StatusVariant = 'active' | 'completed' | 'idle' | 'failed' | 'warning';

interface StatusDotProps {
  status: StatusVariant;
  ping?: boolean;
  className?: string;
}

export const StatusDot: React.FC<StatusDotProps> = ({ status, ping = true, className = '' }) => {
  const getColors = () => {
    switch (status) {
      case 'active':
      case 'completed':
        return { dot: 'bg-emerald-400', ping: 'bg-emerald-400' };
      case 'idle':
        return { dot: 'bg-zinc-500', ping: 'bg-zinc-400' };
      case 'warning':
        return { dot: 'bg-amber-400', ping: 'bg-amber-400' };
      case 'failed':
        return { dot: 'bg-rose-500', ping: 'bg-rose-400' };
      default:
        return { dot: 'bg-cyan-400', ping: 'bg-cyan-400' };
    }
  };

  const { dot, ping: pingColor } = getColors();

  return (
    <span className={`relative flex h-2 w-2 items-center justify-center ${className}`}>
      {ping && status === 'active' && (
        <span className={`absolute inline-flex h-full w-full animate-ping rounded-full ${pingColor} opacity-75`} />
      )}
      <span className={`relative inline-flex h-2 w-2 rounded-full ${dot}`} />
    </span>
  );
};
