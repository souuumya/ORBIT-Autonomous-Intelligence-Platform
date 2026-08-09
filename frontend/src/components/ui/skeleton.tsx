import React from 'react';

interface SkeletonProps {
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '' }) => {
  return <div className={`animate-pulse rounded-md bg-zinc-800/60 ${className}`} />;
};

export const CardSkeleton: React.FC = () => {
  return (
    <div className="rounded-xl border border-zinc-800/60 bg-zinc-950/40 p-5 space-y-4">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-full" />
      <Skeleton className="h-4 w-2/3" />
    </div>
  );
};
