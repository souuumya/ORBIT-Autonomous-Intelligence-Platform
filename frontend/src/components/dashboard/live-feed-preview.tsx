import React from 'react';
import Link from 'next/link';
import { Rss, ArrowUpRight } from 'lucide-react';
import { FormattedTime } from '@/components/ui/formatted-time';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FeedEntryItem } from '@/types/mission-control';

interface LiveFeedPreviewProps {
  entries: FeedEntryItem[];
}

export const LiveFeedPreview: React.FC<LiveFeedPreviewProps> = ({ entries }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Rss className="h-4 w-4 text-cyan-400" />
          <span>Autonomous Progress Feed</span>
        </CardTitle>
        <Link
          href="/dashboard"
          className="flex items-center space-x-1 text-xs text-cyan-400 hover:text-cyan-300 transition"
        >
          <span>Live Stream</span>
          <ArrowUpRight className="h-3 w-3" />
        </Link>
      </CardHeader>

      {entries.length === 0 ? (
        <div className="py-8 text-center text-xs text-zinc-500">
          <p className="font-medium text-zinc-400">Awaiting Feed Events</p>
          <p className="text-[11px] mt-0.5">Real-time progress updates will appear here when an active mission runs.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {entries.slice(0, 4).map((item) => (
            <div
              key={item.id}
              className="rounded-lg border border-zinc-900 bg-zinc-900/30 p-3 text-xs space-y-1.5 hover:border-zinc-800 transition"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Badge variant="cyan" className="text-[10px] py-0 px-1.5">
                    {item.current_stage}
                  </Badge>
                  <span className="font-medium text-zinc-300">{item.agent_responsible}</span>
                </div>
                <FormattedTime isoTimestamp={item.timestamp} className="font-mono text-[10px] text-zinc-500" />
              </div>

              <p className="text-zinc-200 leading-normal">{item.summary_of_work}</p>

              {item.decision_made && (
                <div className="text-[11px] text-zinc-400 font-mono">
                  <span className="text-zinc-500">Decision:</span> {item.decision_made}
                </div>
              )}

              {item.reflection && (
                <div className="mt-1 rounded bg-zinc-950/80 p-2 text-[10px] text-emerald-400/90 font-mono border border-emerald-500/10">
                  <span className="text-emerald-500 uppercase font-semibold">Reflection:</span> {item.reflection}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};

