import React from 'react';
import { Activity, Percent } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';

interface MissionProgressCardProps {
  progressPercentage: number;
  currentStage: string;
  currentAgent: string;
}

export const MissionProgressCard: React.FC<MissionProgressCardProps> = ({
  progressPercentage,
  currentStage,
  currentAgent,
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Activity className="h-4 w-4 text-cyan-400" />
          <span>Execution Progress</span>
        </CardTitle>
        <span className="font-mono text-xs text-cyan-400 font-semibold">
          {progressPercentage.toFixed(1)}%
        </span>
      </CardHeader>

      <div className="space-y-4">
        {/* Progress Bar Container */}
        <div>
          <div className="flex justify-between text-xs text-zinc-400 mb-1.5 font-mono">
            <span>{currentStage}</span>
            <span>{progressPercentage}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-900 border border-zinc-800">
            <div
              className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 transition-all duration-500 ease-out rounded-full"
              style={{ width: `${Math.min(100, Math.max(0, progressPercentage))}%` }}
            />
          </div>
        </div>

        <div className="flex items-center justify-between border-t border-zinc-900 pt-3 text-xs text-zinc-400">
          <span>Responsible Agent:</span>
          <span className="font-semibold text-zinc-200">{currentAgent}</span>
        </div>
      </div>
    </Card>
  );
};
