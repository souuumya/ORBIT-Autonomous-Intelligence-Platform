'use client';

import React, { Suspense } from 'react';
import { MemoryLearningView } from '@/components/memory/memory-learning-view';
import { AppShell } from '@/components/shell';

export default function MemoryPage() {
  return (
    <Suspense
      fallback={
        <AppShell font-mono text-xs text-zinc-500>
          <div className="py-12 text-center text-xs text-zinc-500 font-mono">
            Loading Memory Engine...
          </div>
        </AppShell>
      }
    >
      <MemoryLearningView />
    </Suspense>
  );
}
