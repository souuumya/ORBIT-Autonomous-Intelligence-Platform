import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
}

export const Card: React.FC<CardProps> = ({ children, className = '', glow = false }) => {
  return (
    <div
      className={`relative overflow-hidden rounded-xl border border-zinc-800/80 bg-zinc-950/60 p-5 backdrop-blur-md transition-all duration-300 hover:border-zinc-700/80 ${
        glow ? 'shadow-lg shadow-cyan-500/5' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => <div className={`mb-4 flex items-center justify-between border-b border-zinc-900 pb-3 ${className}`}>{children}</div>;

export const CardTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => <h3 className={`text-sm font-semibold tracking-wide text-zinc-100 uppercase ${className}`}>{children}</h3>;
