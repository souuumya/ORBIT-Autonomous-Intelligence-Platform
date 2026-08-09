import React from 'react';

export type BadgeVariant = 'default' | 'cyan' | 'emerald' | 'amber' | 'rose' | 'outline';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'default', className = '' }) => {
  const getStyles = () => {
    switch (variant) {
      case 'cyan':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
      case 'emerald':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'amber':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'rose':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      case 'outline':
        return 'border-zinc-700 bg-transparent text-zinc-300';
      default:
        return 'bg-zinc-800/60 text-zinc-300 border-zinc-700/50';
    }
  };

  return (
    <span
      className={`inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-medium tracking-wide transition-colors ${getStyles()} ${className}`}
    >
      {children}
    </span>
  );
};
