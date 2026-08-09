'use client';

import React from 'react';
import { AppShell } from '@/components/shell';
import { Settings, Shield, Cpu, Database } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';

export default function SettingsPage() {
  return (
    <AppShell>
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-900 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-100 sm:text-2xl flex items-center space-x-2">
            <Settings className="h-6 w-6 text-cyan-400" />
            <span>Platform Settings</span>
          </h1>
          <p className="text-xs text-zinc-400">
            System configuration, agent parameters, and event bus settings
          </p>
        </div>
      </div>

      <div className="max-w-3xl space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Cpu className="h-4 w-4 text-cyan-400" />
              <span>Orchestrator Configuration</span>
            </CardTitle>
          </CardHeader>
          <div className="space-y-3 text-xs text-zinc-300">
            <div className="flex items-center justify-between border-b border-zinc-900 pb-2">
              <span>Global Execution Timeout</span>
              <span className="font-mono text-cyan-400">300 seconds</span>
            </div>
            <div className="flex items-center justify-between border-b border-zinc-900 pb-2">
              <span>Max Per-Stage Retries</span>
              <span className="font-mono text-cyan-400">3 attempts</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Max Self-Review Revisions</span>
              <span className="font-mono text-cyan-400">2 loops</span>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Database className="h-4 w-4 text-emerald-400" />
              <span>Database & Memory Settings</span>
            </CardTitle>
          </CardHeader>
          <div className="space-y-3 text-xs text-zinc-300">
            <div className="flex items-center justify-between border-b border-zinc-900 pb-2">
              <span>Memory Engine Persistence</span>
              <span className="font-mono text-emerald-400">Enabled</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Event Bus History Retain Count</span>
              <span className="font-mono text-cyan-400">1000 events</span>
            </div>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
