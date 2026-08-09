'use client';

import React, { useState } from 'react';
import { Sidebar } from '@/components/navigation/sidebar';
import { TopStatusBar } from '@/components/navigation/top-status-bar';
import { SystemHealthStatus, MissionStatusType } from '@/types/mission-control';

const DEFAULT_SYSTEM_STATUS: SystemHealthStatus = {
  status: 'ok',
  serviceName: 'Autonomous Intelligence Core',
  timestamp: new Date().toISOString(),
  autonomousWorkerActive: true,
  connectionStatus: 'CONNECTED',
};

interface AppShellProps {
  children: React.ReactNode;
  systemStatus?: SystemHealthStatus;
  currentMissionStatus?: MissionStatusType;
  onInitClick?: () => void;
}

export function AppShell({
  children,
  systemStatus = DEFAULT_SYSTEM_STATUS,
  currentMissionStatus = 'INITIALIZED',
  onInitClick,
}: AppShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-[#090a0f] text-zinc-100 font-sans antialiased">
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col min-w-0">
        <TopStatusBar
          systemStatus={systemStatus}
          currentMissionStatus={currentMissionStatus}
          onMenuToggle={() => setSidebarOpen(!sidebarOpen)}
          onInitClick={onInitClick}
        />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto space-y-6">
          {children}
        </main>
      </div>
    </div>
  );
}

