import React from 'react';
import { GitBranch, CheckCircle, XCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DecisionSummary } from '@/types/mission-control';

interface DecisionSummaryCardProps {
  decision?: DecisionSummary | null;
}

export const DecisionSummaryCard: React.FC<DecisionSummaryCardProps> = ({ decision }) => {
  if (!decision) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <GitBranch className="h-4 w-4 text-cyan-400" />
            <span>Decision Replay Summary</span>
          </CardTitle>
          <Badge variant="outline" className="text-[10px]">
            Plausible Options
          </Badge>
        </CardHeader>

        <div className="py-6 text-center text-xs space-y-1">
          <p className="font-semibold text-zinc-300">Awaiting Decision Phase</p>
          <p className="text-zinc-500 max-w-xs mx-auto text-[11px]">
            Decision Agent will evaluate candidate strategies once planning and research complete.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <GitBranch className="h-4 w-4 text-cyan-400" />
          <span>Decision Replay Summary</span>
        </CardTitle>
        <Badge variant="emerald" className="text-[10px]">
          Score: {(decision.confidenceScore * 100).toFixed(0)}%
        </Badge>
      </CardHeader>

      <div className="space-y-3 text-xs">
        <div>
          <span className="text-[10px] uppercase font-mono tracking-wider text-zinc-500">
            Selected Strategy
          </span>
          <h4 className="text-sm font-semibold text-emerald-400 mt-0.5">
            {decision.selectedStrategyTitle}
          </h4>
          <p className="mt-1 text-zinc-400 leading-relaxed">{decision.reasoning}</p>
        </div>

        <div className="border-t border-zinc-900 pt-3 space-y-2">
          <span className="text-[10px] uppercase font-mono tracking-wider text-zinc-500">
            Evaluated Options ({decision.options.length})
          </span>

          {decision.options.map((opt) => (
            <div
              key={opt.id}
              className={`rounded-lg border p-2.5 flex items-start justify-between ${
                opt.status === 'SELECTED'
                  ? 'border-emerald-500/30 bg-emerald-500/5'
                  : 'border-zinc-900 bg-zinc-900/20 opacity-75'
              }`}
            >
              <div className="space-y-0.5">
                <div className="flex items-center space-x-1.5 font-medium text-zinc-200">
                  {opt.status === 'SELECTED' ? (
                    <CheckCircle className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                  ) : (
                    <XCircle className="h-3.5 w-3.5 text-zinc-500 shrink-0" />
                  )}
                  <span>{opt.title}</span>
                </div>
                <p className="text-[11px] text-zinc-400">{opt.description}</p>
              </div>

              <span className="font-mono text-xs font-semibold text-zinc-300 ml-2">
                {(opt.score * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};

