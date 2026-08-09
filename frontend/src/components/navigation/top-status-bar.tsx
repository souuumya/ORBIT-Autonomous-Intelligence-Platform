'use client';

import React from 'react';
import { Menu, Activity, Wifi, CheckCircle2, Bot } from 'lucide-react';
import { StatusDot } from '@/components/ui/status-dot';
import { Badge } from '@/components/ui/badge';
import { SystemHealthStatus, MissionStatusType } from '@/types/mission-control';

interface TopStatusBarProps {
  systemStatus: SystemHealthStatus;
  currentMissionStatus: MissionStatusType;
  onMenuToggle?: () => void;
  onInitClick?: () => void;
}

export const TopStatusBar: React.FC<TopStatusBarProps> = ({
  systemStatus,
  currentMissionStatus,
  onMenuToggle,
  onInitClick,
}) => {
  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-zinc-800/80 bg-zinc-950/80 px-4 backdrop-blur-xl sm:px-6">
      {/* Left side: Mobile Toggle & Product Name */}
      <div className="flex items-center space-x-3">
        <button
          onClick={onMenuToggle}
          className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-2 text-zinc-400 hover:text-zinc-200 lg:hidden"
          aria-label="Toggle Navigation"
        >
          <Menu className="h-4 w-4" />
        </button>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono tracking-widest text-zinc-400 uppercase hidden sm:inline">
            SYSTEM CONTROL
          </span>
          <span className="text-zinc-600 hidden sm:inline">•</span>
          <div className="flex items-center space-x-1.5">
            <Bot className="h-4 w-4 text-cyan-400" />
            <span className="text-sm font-semibold tracking-wide text-zinc-100">ORBIT ENGINE</span>
          </div>
        </div>
      </div>

      {/* Right side: Autonomous Status, Mission Status, Health, Connection, Init Button */}
      <div className="flex items-center space-x-2 sm:space-x-4 text-xs">
        {onInitClick && (
          <button
            onClick={onInitClick}
            className="rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-[11px] font-semibold text-cyan-300 hover:bg-cyan-500/20 transition-all"
          >
            + Initialize Mission
          </button>
        )}

        {/* Autonomous Worker Status */}
        <div className="hidden md:flex items-center space-x-2 rounded-full border border-cyan-500/20 bg-cyan-500/10 px-3 py-1 text-cyan-300">
          <StatusDot status="active" />
          <span className="font-mono text-[11px] uppercase tracking-wider">AUTONOMOUS</span>
        </div>

        {/* Current Mission Status */}
        <div className="flex items-center space-x-1.5 rounded-md border border-zinc-800 bg-zinc-900/60 px-2.5 py-1">
          <span className="text-zinc-400 font-mono text-[11px]">MISSION:</span>
          <Badge
            variant={
              currentMissionStatus === 'COMPLETED'
                ? 'emerald'
                : currentMissionStatus === 'FAILED'
                ? 'rose'
                : currentMissionStatus === 'INITIALIZED'
                ? 'outline'
                : 'cyan'
            }
            className="text-[10px]"
          >
            {currentMissionStatus}
          </Badge>
        </div>

        {/* System Health */}
        <div className="hidden lg:flex items-center space-x-1.5 text-zinc-400">
          <Activity className="h-3.5 w-3.5 text-emerald-400" />
          <span className="text-zinc-300 font-mono text-[11px]">HEALTH:</span>
          <span className="text-emerald-400 font-semibold text-[11px]">OK</span>
        </div>

        {/* Connection Status */}
        <div className="flex items-center space-x-1.5 text-zinc-400">
          <Wifi className="h-3.5 w-3.5 text-cyan-400" />
          <span className="hidden xl:inline text-zinc-300 font-mono text-[11px]">STATUS:</span>
          <span className="text-cyan-400 font-medium text-[11px]">{systemStatus.connectionStatus}</span>
        </div>
      </div>
    </header>
  );
};

