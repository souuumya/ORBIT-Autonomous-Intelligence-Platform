import React from 'react';
import { History } from 'lucide-react';
import { FormattedTime } from '@/components/ui/formatted-time';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';
import { FeedEntryItem } from '@/types/mission-control';

interface ActivityTimelineProps {
  entries: FeedEntryItem[];
}

export const ActivityTimeline: React.FC<ActivityTimelineProps> = ({ entries }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <History className="h-4 w-4 text-cyan-400" />
          <span>Activity Timeline</span>
        </CardTitle>
        <span className="text-xs font-mono text-zinc-500">{entries.length} Events</span>
      </CardHeader>

      {entries.length === 0 ? (
        <div className="py-6 text-center text-xs text-zinc-500">
          <p className="font-medium text-zinc-400">Timeline Idle</p>
          <p className="text-[11px] mt-0.5">Chronological events will be recorded as stages complete.</p>
        </div>
      ) : (
        <div className="relative pl-4 space-y-4 border-l border-zinc-800/80 my-2">
          {entries.map((item) => (
            <div key={item.id} className="relative text-xs space-y-0.5">
              {/* Timeline Dot */}
              <div className="absolute -left-[21px] top-0.5 h-2.5 w-2.5 rounded-full border border-zinc-950 bg-cyan-400" />

              <div className="flex items-center justify-between text-zinc-400">
                <span className="font-semibold text-zinc-200">{item.current_stage}</span>
                <FormattedTime isoTimestamp={item.timestamp} className="font-mono text-[10px] text-zinc-500" />
              </div>

              <p className="text-zinc-300 text-[11px] leading-snug">{item.summary_of_work}</p>
              <p className="text-[10px] font-mono text-zinc-500">Agent: {item.agent_responsible}</p>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};

