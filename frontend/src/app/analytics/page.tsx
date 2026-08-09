'use client';

import React from 'react';
import { AppShell } from '@/components/shell';
import { BarChart3 } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';

export default function AnalyticsPage() {
  return (
    <AppShell>
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-900 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-100 sm:text-2xl flex items-center space-x-2">
            <BarChart3 className="h-6 w-6 text-cyan-400" />
            <span>Platform Analytics</span>
          </h1>
          <p className="text-xs text-zinc-400">
            Performance analytics, execution metrics, and quality score distribution
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Average Quality Score</CardTitle>
          </CardHeader>
          <div className="text-2xl font-bold text-emerald-400 font-mono">95.4%</div>
          <p className="text-xs text-zinc-400 mt-1">Across completed autonomous missions</p>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Pipeline Efficiency</CardTitle>
          </CardHeader>
          <div className="text-2xl font-bold text-cyan-400 font-mono">2.8s</div>
          <p className="text-xs text-zinc-400 mt-1">Average mission execution latency</p>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Self-Correction Loop</CardTitle>
          </CardHeader>
          <div className="text-2xl font-bold text-amber-400 font-mono">0.0%</div>
          <p className="text-xs text-zinc-400 mt-1">Revision trigger frequency</p>
        </Card>
      </div>
    </AppShell>
  );
}
