import React from 'react';
import { Target, Clock, Shield, Flag } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MissionDetail } from '@/types/mission-control';

import { FormattedTime } from '@/components/ui/formatted-time';

interface MissionStatusCardProps {
  mission: MissionDetail;
}

export const MissionStatusCard: React.FC<MissionStatusCardProps> = ({ mission }) => {
  return (
    <Card glow>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Target className="h-4 w-4 text-cyan-400" />
          <span>Active Mission Context</span>
        </CardTitle>
        <Badge
          variant={
            mission.status === 'COMPLETED'
              ? 'emerald'
              : mission.status === 'FAILED'
              ? 'rose'
              : 'cyan'
          }
        >
          {mission.status}
        </Badge>
      </CardHeader>

      <div className="space-y-3">
        <div>
          <h2 className="text-lg font-semibold text-zinc-100">{mission.title}</h2>
          <p className="mt-1 text-xs text-zinc-400 leading-relaxed">{mission.objective}</p>
        </div>

        <div className="grid grid-cols-2 gap-3 border-t border-zinc-900 pt-3 text-xs">
          <div className="flex items-center space-x-2 text-zinc-400">
            <Clock className="h-3.5 w-3.5 text-zinc-500" />
            <span>Started:</span>
            <FormattedTime isoTimestamp={mission.startedAt} className="font-mono text-zinc-300" />
          </div>

          <div className="flex items-center space-x-2 text-zinc-400">
            <Shield className="h-3.5 w-3.5 text-zinc-500" />
            <span>Priority:</span>
            <span className="font-mono uppercase text-cyan-400">{mission.priority}</span>
          </div>

          <div className="flex items-center space-x-2 text-zinc-400">
            <Flag className="h-3.5 w-3.5 text-zinc-500" />
            <span>Current Stage:</span>
            <span className="font-semibold text-zinc-200">{mission.currentStage}</span>
          </div>

          <div className="flex items-center space-x-2 text-zinc-400">
            <span className="font-mono text-zinc-500">ID:</span>
            <span className="font-mono text-[11px] text-zinc-300">{mission.id}</span>
          </div>
        </div>
      </div>
    </Card>
  );
};
