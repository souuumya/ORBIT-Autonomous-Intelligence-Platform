import React from 'react';
import { Cpu, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';
import { AgentNode } from '@/types/mission-control';

interface AgentActivityPanelProps {
  nodes: AgentNode[];
}

export const AgentActivityPanel: React.FC<AgentActivityPanelProps> = ({ nodes }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Cpu className="h-4 w-4 text-cyan-400" />
          <span>Active Agent Status</span>
        </CardTitle>
        <span className="text-xs font-mono text-zinc-500">{nodes.length} Registered</span>
      </CardHeader>

      <div className="divide-y divide-zinc-900">
        {nodes.map((node) => (
          <div key={node.id} className="flex items-center justify-between py-2.5 first:pt-0 last:pb-0">
            <div className="flex items-center space-x-3">
              <div className="flex h-7 w-7 items-center justify-center rounded bg-zinc-900 border border-zinc-800 text-zinc-400">
                {node.status === 'completed' && <CheckCircle2 className="h-4 w-4 text-emerald-400" />}
                {node.status === 'active' && <Loader2 className="h-4 w-4 text-cyan-400 animate-spin" />}
                {node.status === 'failed' && <AlertCircle className="h-4 w-4 text-rose-400" />}
                {node.status === 'idle' && <span className="h-2 w-2 rounded-full bg-zinc-600" />}
              </div>
              <div>
                <p className="text-xs font-medium text-zinc-200">{node.name}</p>
                <p className="text-[10px] text-zinc-500 font-mono">{node.role}</p>
              </div>
            </div>

            <div className="text-right">
              <span
                className={`text-[11px] font-mono capitalize ${
                  node.status === 'completed'
                    ? 'text-emerald-400'
                    : node.status === 'active'
                    ? 'text-cyan-400 font-semibold'
                    : node.status === 'failed'
                    ? 'text-rose-400'
                    : 'text-zinc-500'
                }`}
              >
                {node.status}
              </span>
              {node.durationMs && (
                <p className="text-[9px] text-zinc-600 font-mono">{node.durationMs}ms</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};
