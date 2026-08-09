'use client';

import React, { useState } from 'react';
import { AppShell } from '@/components/shell';
import { AgentNetwork } from '@/components/agent-visualization/agent-network';
import { MissionStatusCard } from '@/components/dashboard/mission-status-card';
import { MissionProgressCard } from '@/components/dashboard/mission-progress-card';
import { AgentActivityPanel } from '@/components/dashboard/agent-activity-panel';
import { LiveFeedPreview } from '@/components/dashboard/live-feed-preview';
import { DecisionSummaryCard } from '@/components/dashboard/decision-summary-card';
import { MemorySummaryCard } from '@/components/dashboard/memory-summary-card';
import { ActivityTimeline } from '@/components/dashboard/activity-timeline';
import { MissionInitModal } from '@/components/dashboard/mission-init-modal';
import { ErrorBanner } from '@/components/ui/error-banner';
import { useMissionFeed } from '@/hooks/use-mission-feed';
import { Activity, Sparkles, Plus, Bot } from 'lucide-react';
import { Card } from '@/components/ui/card';

export function DashboardView() {
  const [initModalOpen, setInitModalOpen] = useState(false);

  const {
    mission,
    feedItems,
    agentNodes,
    decisionSummary,
    memorySummary,
    systemStatus,
    isInitializing,
    error,
    initializeMission,
    resetMission,
  } = useMissionFeed();

  const activeNode = agentNodes.find((n) => n.status === 'active')?.id;

  return (
    <AppShell
      systemStatus={systemStatus}
      currentMissionStatus={mission ? mission.status : 'INITIALIZED'}
      onInitClick={() => setInitModalOpen(true)}
    >
      {/* Top Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-900 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold tracking-tight text-zinc-100 sm:text-2xl">
              Mission Control Dashboard
            </h1>
            {mission ? (
              <span className="flex items-center space-x-1 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2.5 py-0.5 text-[10px] font-mono text-cyan-300">
                <Activity className="h-3 w-3 animate-pulse" />
                <span>OBSERVING REAL BACKEND</span>
              </span>
            ) : (
              <span className="rounded-full border border-zinc-800 bg-zinc-900 px-2.5 py-0.5 text-[10px] font-mono text-zinc-400">
                IDLE RUNTIME
              </span>
            )}
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Real-time autonomous intelligence core monitoring & multi-agent pipeline observer
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {mission && (
            <button
              onClick={resetMission}
              className="rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs font-medium text-zinc-400 hover:text-zinc-200 transition"
            >
              Clear Observer
            </button>
          )}
          <button
            onClick={() => setInitModalOpen(true)}
            className="flex items-center space-x-1.5 rounded-lg border border-cyan-500/40 bg-cyan-500/10 px-3.5 py-1.5 text-xs font-semibold text-cyan-300 hover:bg-cyan-500/20 transition-all shadow-sm shadow-cyan-500/10"
          >
            <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
            <span>+ Initialize Mission</span>
          </button>
        </div>
      </div>

      {/* Connection / Backend Error Notification */}
      {error && <ErrorBanner message={`Backend Notice: ${error}`} />}

      {/* Empty State Banner when no active mission */}
      {!mission && (
        <Card glow className="border-cyan-500/20 bg-gradient-to-r from-zinc-950 via-zinc-900/60 to-zinc-950 p-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-center sm:text-left">
            <div className="flex items-center space-x-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-cyan-500/30 bg-cyan-500/10 text-cyan-400">
                <Bot className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-zinc-100">NO ACTIVE MISSION</h3>
                <p className="text-xs text-zinc-400 max-w-lg mt-0.5">
                  The autonomous runtime is currently idle. Initialize a mission to observe real multi-agent pipeline execution in real time.
                </p>
              </div>
            </div>
            <button
              onClick={() => setInitModalOpen(true)}
              className="flex items-center space-x-2 rounded-lg border border-cyan-500/40 bg-gradient-to-r from-cyan-600 to-cyan-500 px-5 py-2.5 text-xs font-bold text-zinc-950 hover:from-cyan-500 hover:to-cyan-400 transition shadow-lg shadow-cyan-500/20 shrink-0"
            >
              <Plus className="h-4 w-4 text-zinc-950" />
              <span>Initialize Mission</span>
            </button>
          </div>
        </Card>
      )}

      {/* Agent Network Visualization */}
      <AgentNetwork nodes={agentNodes} activeNodeId={activeNode} />

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Column: Active Mission & Progress */}
        <div className="space-y-6 lg:col-span-2">
          {mission ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <MissionStatusCard mission={mission} />
              <MissionProgressCard
                progressPercentage={mission.progressPercentage}
                currentStage={mission.currentStage}
                currentAgent={mission.currentAgent}
              />
            </div>
          ) : (
            <Card>
              <div className="py-8 text-center text-xs space-y-1">
                <p className="font-semibold text-zinc-300">Awaiting Mission Context</p>
                <p className="text-zinc-500 max-w-xs mx-auto text-[11px]">
                  Initialize a mission to view real-time stage status and execution progress.
                </p>
              </div>
            </Card>
          )}

          <LiveFeedPreview entries={feedItems} />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <DecisionSummaryCard decision={decisionSummary} />
            <MemorySummaryCard memory={memorySummary} />
          </div>
        </div>

        {/* Right Column: Active Agents & Activity Timeline */}
        <div className="space-y-6">
          <AgentActivityPanel nodes={agentNodes} />
          <ActivityTimeline entries={feedItems} />
        </div>
      </div>

      {/* Mission Initialization Modal */}
      <MissionInitModal
        isOpen={initModalOpen}
        onClose={() => setInitModalOpen(false)}
        onSubmit={initializeMission}
        isInitializing={isInitializing}
      />
    </AppShell>
  );
}
