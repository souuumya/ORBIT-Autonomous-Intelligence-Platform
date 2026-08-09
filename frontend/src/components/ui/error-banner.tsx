import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ message, onRetry }) => {
  return (
    <div className="flex items-center justify-between rounded-lg border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-xs text-rose-300">
      <div className="flex items-center space-x-2">
        <AlertTriangle className="h-4 w-4 shrink-0 text-rose-400" />
        <span>{message}</span>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center space-x-1 rounded bg-rose-500/20 px-2.5 py-1 text-[11px] font-medium text-rose-200 hover:bg-rose-500/30 transition"
        >
          <RefreshCw className="h-3 w-3" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
};
