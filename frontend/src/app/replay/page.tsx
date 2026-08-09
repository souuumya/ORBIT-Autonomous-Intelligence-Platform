'use client';

import React, { Suspense } from 'react';
import { DecisionReplayView } from '@/components/replay/decision-replay-view';
import { AppShell } from '@/components/shell';

export default function DecisionReplayPage() {
  return (
    <Suspense
      fallback={
        <AppShell>
          <div className="py-12 text-center text-xs text-zinc-500 font-mono">
            Loading Decision Replay...
          </div>
        </AppShell>
      }
    >
      <DecisionReplayView />
    </Suspense>
  );
}
