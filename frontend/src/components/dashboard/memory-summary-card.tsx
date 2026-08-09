import React from 'react';
import { Brain, Sparkles, BookOpen } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';
import { MemorySummary } from '@/types/mission-control';

interface MemorySummaryCardProps {
  memory?: MemorySummary | null;
}

export const MemorySummaryCard: React.FC<MemorySummaryCardProps> = ({ memory }) => {
  if (!memory) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Brain className="h-4 w-4 text-cyan-400" />
            <span>Long-Term Memory & Insights</span>
          </CardTitle>
          <span className="text-xs font-mono text-zinc-500">0 Records</span>
        </CardHeader>

        <div className="py-6 text-center text-xs space-y-1">
          <p className="font-semibold text-zinc-300">Awaiting Reflection Phase</p>
          <p className="text-zinc-500 max-w-xs mx-auto text-[11px]">
            Reflection Engine will synthesize post-mission performance self-review and persist insights upon completion.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Brain className="h-4 w-4 text-cyan-400" />
          <span>Long-Term Memory & Insights</span>
        </CardTitle>
        <span className="text-xs font-mono text-zinc-500">{memory.totalRecords} Records</span>
      </CardHeader>

      <div className="space-y-3 text-xs">
        <div className="grid grid-cols-2 gap-2 text-center">
          <div className="rounded-lg border border-zinc-900 bg-zinc-900/40 p-2.5">
            <span className="text-[10px] uppercase font-mono text-zinc-500">Insights</span>
            <p className="text-base font-semibold text-cyan-400">{memory.insightsCount}</p>
          </div>
          <div className="rounded-lg border border-zinc-900 bg-zinc-900/40 p-2.5">
            <span className="text-[10px] uppercase font-mono text-zinc-500">Reflections</span>
            <p className="text-base font-semibold text-emerald-400">{memory.reflectionsCount}</p>
          </div>
        </div>

        <div className="border-t border-zinc-900 pt-3 space-y-2">
          <span className="text-[10px] uppercase font-mono tracking-wider text-zinc-500">
            Recent Lessons Learned
          </span>

          {memory.recentLessons.map((item) => (
            <div key={item.id} className="rounded-lg border border-zinc-900 bg-zinc-900/30 p-2.5 space-y-1">
              <div className="flex items-center justify-between text-zinc-300 font-medium">
                <span className="flex items-center space-x-1.5">
                  <Sparkles className="h-3 w-3 text-cyan-400 shrink-0" />
                  <span>{item.summary}</span>
                </span>
                <span className="font-mono text-[10px] text-emerald-400">
                  {(item.confidenceScore * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-[11px] text-zinc-400 leading-normal">{item.insight}</p>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};

