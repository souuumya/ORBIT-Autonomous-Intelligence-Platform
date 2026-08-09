'use client';

import React, { useState } from 'react';
import { AppShell } from '@/components/shell';
import { Target, Plus } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MissionInitModal } from '@/components/dashboard/mission-init-modal';
import { useMissionFeed } from '@/hooks/use-mission-feed';
import Link from 'next/link';

export default function MissionsPage() {
  const [initModalOpen, setInitModalOpen] = useState(false);
  const { mission, initializeMission, isInitializing, systemStatus } = useMissionFeed();

  const missions = mission ? [mission] : [];

  return (
    <AppShell
      systemStatus={systemStatus}
      currentMissionStatus={mission ? mission.status : 'INITIALIZED'}
      onInitClick={() => setInitModalOpen(true)}
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-900 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-100 sm:text-2xl flex items-center space-x-2">
            <Target className="h-6 w-6 text-cyan-400" />
            <span>Missions Overview</span>
          </h1>
          <p className="text-xs text-zinc-400">
            Manage autonomous missions and track multi-agent lifecycle execution
          </p>
        </div>
        <button
          onClick={() => setInitModalOpen(true)}
          className="flex items-center space-x-1.5 rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-3.5 py-1.5 text-xs font-semibold text-cyan-300 hover:bg-cyan-500/20 transition-all"
        >
          <Plus className="h-3.5 w-3.5" />
          <span>New Mission</span>
        </button>
      </div>

      <div className="space-y-4">
        {missions.length === 0 ? (
          <Card>
            <div className="py-12 text-center text-xs space-y-2">
              <p className="font-semibold text-zinc-300">No Active Missions</p>
              <p className="text-zinc-500 max-w-sm mx-auto text-[11px]">
                No autonomous missions are currently running. Click &quot;New Mission&quot; above to initialize a pipeline.
              </p>
              <button
                onClick={() => setInitModalOpen(true)}
                className="mt-2 inline-flex items-center space-x-1 rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-3.5 py-1.5 text-xs font-semibold text-cyan-300 hover:bg-cyan-500/20 transition-all"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Initialize Mission</span>
              </button>
            </div>
          </Card>
        ) : (
          missions.map((m) => (
            <Card key={m.id} glow>
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <h3 className="text-base font-semibold text-zinc-100">{m.title}</h3>
                    <Badge
                      variant={
                        m.status === 'COMPLETED'
                          ? 'emerald'
                          : m.status === 'FAILED'
                          ? 'rose'
                          : 'cyan'
                      }
                    >
                      {m.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-zinc-400 max-w-2xl">{m.objective}</p>
                </div>

                <div className="flex items-center space-x-4 text-xs text-zinc-400 font-mono">
                  <div>
                    <span className="text-zinc-500 text-[10px] block">PRIORITY</span>
                    <span className="uppercase text-cyan-400 font-semibold">{m.priority}</span>
                  </div>
                  <div>
                    <span className="text-zinc-500 text-[10px] block">PROGRESS</span>
                    <span className="text-zinc-200">{m.progressPercentage.toFixed(0)}%</span>
                  </div>
                  <div>
                    <span className="text-zinc-500 text-[10px] block">MISSION ID</span>
                    <span className="text-zinc-300 text-[11px]">{m.id}</span>
                  </div>
                  <div>
                    <Link
                      href="/dashboard"
                      className="inline-block rounded border border-cyan-500/30 bg-cyan-500/10 px-2.5 py-1 text-[11px] font-sans font-medium text-cyan-300 hover:bg-cyan-500/20 transition"
                    >
                      Observe
                    </Link>
                  </div>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>


      <MissionInitModal
        isOpen={initModalOpen}
        onClose={() => setInitModalOpen(false)}
        onSubmit={initializeMission}
        isInitializing={isInitializing}
      />
    </AppShell>
  );
}

