'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Target,
  RotateCcw,
  Brain,
  BarChart3,
  Settings,
  ShieldCheck,
  ChevronRight,
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const pathname = usePathname();

  const navItems = [
    { name: 'Mission Control', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Missions', href: '/missions', icon: Target },
    { name: 'Decision Replay', href: '/replay', icon: RotateCcw },
    { name: 'Memory', href: '/memory', icon: Brain },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed top-0 left-0 z-50 flex h-full w-64 flex-col border-r border-zinc-800/80 bg-zinc-950/95 backdrop-blur-xl transition-transform duration-300 lg:static lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="flex h-16 items-center justify-between border-b border-zinc-900 px-6">
          <Link href="/dashboard" className="flex items-center space-x-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-cyan-500/30 bg-cyan-500/10 text-cyan-400">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div>
              <span className="text-sm font-semibold tracking-wider text-zinc-100 uppercase">ORBIT</span>
              <span className="ml-1.5 text-[10px] font-mono tracking-widest text-cyan-400">CORE</span>
            </div>
          </Link>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 space-y-1 px-3 py-6">
          <div className="mb-2 px-3 text-[10px] font-semibold tracking-widest text-zinc-400 uppercase">
            Platform Navigation
          </div>

          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || (item.href === '/dashboard' && pathname === '/');

            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={onClose}
                className={`group flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium transition-all duration-200 ${
                  isActive
                    ? 'border border-cyan-500/20 bg-cyan-500/10 text-cyan-300 shadow-sm shadow-cyan-500/5'
                    : 'text-zinc-400 hover:bg-zinc-900/60 hover:text-zinc-200'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`h-4 w-4 ${isActive ? 'text-cyan-400' : 'text-zinc-500 group-hover:text-zinc-300'}`} />
                  <span>{item.name}</span>
                </div>
                {isActive && <ChevronRight className="h-3 w-3 text-cyan-400/70" />}
              </Link>
            );
          })}
        </nav>

        {/* Footer info */}
        <div className="border-t border-zinc-900 p-4">
          <div className="rounded-lg border border-zinc-900 bg-zinc-900/40 p-3">
            <div className="flex items-center justify-between text-[11px] text-zinc-400">
              <span>Engine Status</span>
              <span className="flex items-center space-x-1 text-emerald-400">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span>Autonomous</span>
              </span>
            </div>
            <p className="mt-1 text-[10px] text-zinc-500 font-mono">v1.0.0 • Hackathon Evaluation</p>
          </div>
        </div>
      </aside>
    </>
  );
};
