'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  Compass,
  FileSearch,
  GitBranch,
  Sparkles,
  CheckCheck,
  BrainCircuit,
  Flag,
  ArrowRight,
} from 'lucide-react';
import { AgentNode, AgentNodeStatus } from '@/types/mission-control';
import { StatusDot } from '@/components/ui/status-dot';

interface AgentNetworkProps {
  nodes: AgentNode[];
  activeNodeId?: string;
  className?: string;
}

export const AgentNetwork: React.FC<AgentNetworkProps> = ({
  nodes,
  activeNodeId,
  className = '',
}) => {
  const getNodeIcon = (role: string) => {
    switch (role.toLowerCase()) {
      case 'orchestrator':
        return Flag;
      case 'planner':
        return Compass;
      case 'research':
        return FileSearch;
      case 'decision':
        return GitBranch;
      case 'creator':
        return Sparkles;
      case 'reviewer':
        return CheckCheck;
      case 'engine':
      case 'memory':
        return BrainCircuit;
      default:
        return Compass;
    }
  };

  const getStatusColor = (status: AgentNodeStatus) => {
    switch (status) {
      case 'active':
        return 'border-cyan-500/60 bg-cyan-500/10 text-cyan-300 shadow-md shadow-cyan-500/10';
      case 'completed':
        return 'border-emerald-500/30 bg-emerald-500/5 text-emerald-300';
      case 'failed':
        return 'border-rose-500/40 bg-rose-500/10 text-rose-300';
      default:
        return 'border-zinc-800/80 bg-zinc-900/40 text-zinc-500';
    }
  };

  return (
    <div className={`w-full max-w-full overflow-hidden rounded-xl border border-zinc-800/80 bg-zinc-950/60 p-4 sm:p-5 backdrop-blur-md ${className}`}>
      {/* Header */}
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="text-xs sm:text-sm font-semibold tracking-wider text-zinc-100 uppercase">
            AUTONOMOUS AGENT PIPELINE
          </h3>
          <p className="text-[11px] text-zinc-400">Sequential multi-agent handoff graph</p>
        </div>
        <div className="flex items-center space-x-3 text-[11px] text-zinc-400">
          <span className="flex items-center space-x-1">
            <StatusDot status="completed" ping={false} />
            <span>Completed</span>
          </span>
          <span className="flex items-center space-x-1">
            <StatusDot status="active" />
            <span>Active</span>
          </span>
          <span className="flex items-center space-x-1">
            <StatusDot status="idle" ping={false} />
            <span>Idle</span>
          </span>
        </div>
      </div>

      {/* Controlled Horizontal Flow Container */}
      <div className="w-full max-w-full overflow-x-auto overflow-y-hidden py-2 px-1">
        <div className="flex items-center justify-between min-w-max lg:min-w-0 w-full gap-1 sm:gap-2">
          {nodes.map((node, index) => {
            const Icon = getNodeIcon(node.role);
            const isLast = index === nodes.length - 1;
            const isActive = node.id === activeNodeId || node.status === 'active';

            return (
              <React.Fragment key={node.id}>
                {/* Node Card */}
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25, delay: index * 0.04 }}
                  className={`flex flex-col items-center flex-1 min-w-[95px] max-w-[140px] rounded-lg border p-2.5 sm:p-3 text-center transition-all ${getStatusColor(
                    node.status
                  )} ${isActive ? 'ring-1 ring-cyan-500/40 z-10' : ''}`}
                >
                  {/* Node Icon */}
                  <div className="mb-1.5 flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 bg-zinc-900/80 shrink-0">
                    <Icon className="h-4 w-4" />
                  </div>

                  {/* Node Name & Role */}
                  <span className="text-[11px] font-semibold tracking-wide text-zinc-100 truncate w-full">
                    {node.name}
                  </span>
                  <span className="text-[9px] font-mono text-zinc-400 uppercase tracking-wider mt-0.5 truncate w-full">
                    {node.role}
                  </span>

                  {/* Duration Badge */}
                  {node.durationMs && (
                    <span className="mt-1 text-[9px] font-mono text-zinc-500 shrink-0">
                      {node.durationMs}ms
                    </span>
                  )}
                </motion.div>

                {/* Connecting Line / Arrow */}
                {!isLast && (
                  <div className="flex items-center shrink-0 mx-0.5 sm:mx-1">
                    <motion.div
                      animate={node.status === 'completed' ? { opacity: [0.4, 1, 0.4] } : {}}
                      transition={{ repeat: Infinity, duration: 2 }}
                      className="flex items-center text-zinc-600"
                    >
                      <div className="h-[1px] w-3 sm:w-5 bg-gradient-to-r from-zinc-700 to-zinc-800" />
                      <ArrowRight className="h-3 w-3 text-zinc-600 -ml-1 shrink-0" />
                    </motion.div>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
};
