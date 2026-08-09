'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { AppShell } from '@/components/shell';
import {
  RotateCcw,
  GitBranch,
  CheckCircle,
  XCircle,
  ChevronLeft,
  ChevronRight,
  Brain,
  FileSearch,
  Sparkles,
  CheckCheck,
  Compass,
  AlertCircle,
  HelpCircle,
  Layers,
} from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FormattedTime } from '@/components/ui/formatted-time';
import { ErrorBanner } from '@/components/ui/error-banner';
import {
  apiClient,
  ReplayStepData,
  ReplayTimelineResponse,
  ReflectionReportResponse,
} from '@/lib/api-client';
import { MissionStatusType } from '@/types/mission-control';
import { motion, AnimatePresence } from 'framer-motion';

interface MissionItem {
  id: string;
  title: string;
  objective: string;
  status: MissionStatusType;
  priority: string;
  created_at: string;
}

export function DecisionReplayView() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const urlMissionId = searchParams.get('mission_id');

  const [missions, setMissions] = useState<MissionItem[]>([]);
  const [selectedMissionId, setSelectedMissionId] = useState<string | null>(urlMissionId);
  const [timeline, setTimeline] = useState<ReplayTimelineResponse | null>(null);
  const [reflection, setReflection] = useState<ReflectionReportResponse | null>(null);
  const [selectedStepIndex, setSelectedStepIndex] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showWhyGraph, setShowWhyGraph] = useState<boolean>(false);

  // Fetch available missions for selection
  const fetchMissions = useCallback(async () => {
    try {
      const res = await apiClient.listMissions(undefined, 50, 0);
      setMissions(res.missions || []);
      if (!selectedMissionId && res.missions && res.missions.length > 0) {
        const firstId = res.missions[0].id;
        setSelectedMissionId(firstId);
      }
    } catch {
      // Ignore initial load error
    }
  }, [selectedMissionId]);

  useEffect(() => {
    fetchMissions();
  }, [fetchMissions]);

  // Load replay data for selected mission
  const loadReplayData = useCallback(async (missionId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const [replayRes, reflectionRes] = await Promise.all([
        apiClient.getMissionReplay(missionId),
        apiClient.getMissionReflection(missionId),
      ]);

      if (!replayRes || replayRes.steps.length === 0) {
        setTimeline(null);
        setError('Replay data unavailable for this mission.');
      } else {
        setTimeline(replayRes);
        // Find decision step index by default or select first
        const decIdx = replayRes.steps.findIndex(
          (s) => s.action_type === 'DECISION' || s.agent === 'DecisionAgent'
        );
        setSelectedStepIndex(decIdx >= 0 ? decIdx : 0);
      }

      setReflection(reflectionRes);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load replay timeline.';
      setError(msg);
      setTimeline(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedMissionId) {
      loadReplayData(selectedMissionId);
      // Sync URL search params
      const params = new URLSearchParams(window.location.search);
      params.set('mission_id', selectedMissionId);
      router.replace(`/replay?${params.toString()}`, { scroll: false });
    }
  }, [selectedMissionId, loadReplayData, router]);

  const currentMission = missions.find((m) => m.id === selectedMissionId);
  const steps = timeline?.steps || [];
  const currentStep: ReplayStepData | null = steps[selectedStepIndex] || null;

  // Extract Decision Agent data from steps/metadata
  const decisionStep = steps.find(
    (s) => s.action_type === 'DECISION' || s.agent === 'DecisionAgent'
  );
  const rejectedSteps = steps.filter((s) => s.action_type === 'REJECTED_STRATEGY');
  const selectedStep = steps.find((s) => s.action_type === 'SELECTED_STRATEGY');
  const researchStep = steps.find(
    (s) => s.action_type === 'RESEARCH' || s.agent === 'ResearchAgent'
  );

  // Extract selected and rejected info from decision step metadata or individual steps
  const decisionMeta = decisionStep?.metadata || {};
  const selectedStrategy = (decisionMeta.selected_strategy as Record<string, unknown>) ||
    selectedStep?.metadata || { title: selectedStep?.reason || decisionStep?.output_summary };

  const rejectedStrategies = (decisionMeta.rejected_strategies as Array<Record<string, unknown>>) ||
    rejectedSteps.map((s) => ({
      title: (s.metadata?.title as string) || s.output_summary.replace(/^Rejected\s*['"]?|['"]?$/gi, ''),
      reason: s.reason,
      score: s.metadata?.score || s.confidence,
    }));

  const getAgentIcon = (agent: string) => {
    const a = agent.toLowerCase();
    if (a.includes('planner')) return Compass;
    if (a.includes('research')) return FileSearch;
    if (a.includes('decision')) return GitBranch;
    if (a.includes('creator')) return Sparkles;
    if (a.includes('reviewer')) return CheckCheck;
    if (a.includes('memory') || a.includes('reflection')) return Brain;
    return Layers;
  };

  return (
    <AppShell currentMissionStatus={currentMission?.status || 'INITIALIZED'}>
      {/* Top Navigation & Mission Selection Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-900 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-100 sm:text-2xl flex items-center space-x-2">
            <RotateCcw className="h-6 w-6 text-cyan-400" />
            <span>Decision Replay Inspector</span>
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Step-by-step decision auditing, reasoning breakdown, and candidate strategy evaluation
          </p>
        </div>

        {/* Mission Dropdown Selector */}
        <div className="flex items-center space-x-3">
          <label className="text-xs font-mono text-zinc-400 uppercase tracking-wider shrink-0">
            Select Mission:
          </label>
          <select
            value={selectedMissionId || ''}
            onChange={(e) => setSelectedMissionId(e.target.value)}
            className="rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none transition max-w-xs"
          >
            {missions.length === 0 ? (
              <option value="">No missions available</option>
            ) : (
              missions.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.title} ({m.status})
                </option>
              ))
            )}
          </select>
        </div>
      </div>

      {/* Error Banner */}
      {error && <ErrorBanner message={error} />}

      {/* Empty State when no missions exist */}
      {missions.length === 0 && !isLoading && (
        <Card className="py-12 text-center text-xs space-y-2 border-dashed border-zinc-800">
          <div className="flex justify-center">
            <RotateCcw className="h-8 w-8 text-zinc-600" />
          </div>
          <p className="font-semibold text-zinc-300">No Completed Missions Yet</p>
          <p className="text-zinc-500 max-w-sm mx-auto text-[11px]">
            Initialize and complete an autonomous mission to inspect its full decision replay timeline and candidate evaluations.
          </p>
        </Card>
      )}

      {/* Main Replay Grid */}
      {timeline && (
        <div className="space-y-6">
          {/* Mission Overview Banner */}
          {currentMission && (
            <Card glow className="border-cyan-500/20 bg-gradient-to-r from-zinc-950 via-zinc-900/40 to-zinc-950">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <h2 className="text-base font-bold text-zinc-100">{currentMission.title}</h2>
                    <Badge variant={currentMission.status === 'COMPLETED' ? 'emerald' : 'cyan'}>
                      {currentMission.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-zinc-400 max-w-3xl">{currentMission.objective}</p>
                </div>

                <div className="flex items-center space-x-3 text-xs shrink-0">
                  <button
                    onClick={() => setShowWhyGraph(!showWhyGraph)}
                    className="flex items-center space-x-1.5 rounded-lg border border-cyan-500/40 bg-cyan-500/10 px-3.5 py-1.5 text-xs font-semibold text-cyan-300 hover:bg-cyan-500/20 transition shadow-sm shadow-cyan-500/10"
                  >
                    <HelpCircle className="h-3.5 w-3.5 text-cyan-400" />
                    <span>{showWhyGraph ? 'Hide Decision Flow' : 'Why did AI choose this?'}</span>
                  </button>
                </div>
              </div>
            </Card>
          )}

          {/* Signature Moment: Visual Decision Graph */}
          <AnimatePresence>
            {showWhyGraph && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <Card className="border-cyan-500/30 bg-zinc-950/80 p-5 space-y-4">
                  <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                    <h3 className="text-xs font-mono font-bold tracking-wider text-cyan-400 uppercase flex items-center space-x-2">
                      <GitBranch className="h-4 w-4 text-cyan-400" />
                      <span>AUTONOMOUS DECISION RATIONALE FLOW</span>
                    </h3>
                    <span className="text-[10px] font-mono text-zinc-500">Persisted Reasoning Graph</span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
                    {/* Step 1: Research Context */}
                    <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3 space-y-1.5">
                      <span className="text-[10px] font-mono uppercase text-cyan-400 font-semibold block">
                        1. Domain Evidence
                      </span>
                      <p className="font-medium text-zinc-200 text-[11px]">
                        {researchStep?.output_summary || 'Compiled domain evidence brief.'}
                      </p>
                    </div>

                    {/* Step 2: Rejected Alternatives */}
                    <div className="rounded-lg border border-rose-500/30 bg-rose-500/5 p-3 space-y-1.5">
                      <span className="text-[10px] font-mono uppercase text-rose-400 font-semibold block">
                        2. Rejected Alternatives ({rejectedStrategies.length})
                      </span>
                      {rejectedStrategies.length === 0 ? (
                        <p className="text-[11px] text-zinc-500">None rejected.</p>
                      ) : (
                        rejectedStrategies.map((rej, idx) => (
                          <div key={idx} className="text-[10px] text-rose-300 font-mono">
                            ✕ {String(rej.title || 'Alternative')}
                          </div>
                        ))
                      )}
                    </div>

                    {/* Step 3: Selected Strategy */}
                    <div className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-3 space-y-1.5">
                      <span className="text-[10px] font-mono uppercase text-emerald-400 font-semibold block">
                        3. Selected Strategy ✓
                      </span>
                      <p className="font-bold text-emerald-300 text-xs">
                        {String(selectedStrategy.title || decisionStep?.output_summary || 'Optimal Strategy')}
                      </p>
                      <p className="text-[10px] text-zinc-400 leading-snug">{decisionStep?.reason}</p>
                    </div>

                    {/* Step 4: Outcome & Reflection */}
                    <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3 space-y-1.5">
                      <span className="text-[10px] font-mono uppercase text-cyan-400 font-semibold block">
                        4. Reflection & Score
                      </span>
                      <p className="text-[11px] text-zinc-200">
                        Score:{' '}
                        <span className="font-mono text-emerald-400 font-bold">
                          {((reflection?.performance_score || decisionStep?.confidence || 0.95) * 100).toFixed(0)}%
                        </span>
                      </p>
                      <p className="text-[10px] text-zinc-400 leading-snug">
                        {reflection?.lessons_learned?.[0] || 'Performance review completed.'}
                      </p>
                    </div>
                  </div>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Main 2-Column Grid: Timeline & Inspector */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column: Replay Step Timeline */}
            <div className="lg:col-span-1 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <RotateCcw className="h-4 w-4 text-cyan-400" />
                    <span>Chronological Replay</span>
                  </CardTitle>
                  <span className="text-xs font-mono text-zinc-500">{steps.length} Steps</span>
                </CardHeader>

                {/* Step Controls */}
                <div className="flex items-center justify-between border-b border-zinc-900 pb-3 mb-3">
                  <button
                    disabled={selectedStepIndex <= 0}
                    onClick={() => setSelectedStepIndex((i) => Math.max(0, i - 1))}
                    className="flex items-center space-x-1 rounded border border-zinc-800 bg-zinc-900 px-2.5 py-1 text-[11px] font-mono text-zinc-300 hover:bg-zinc-800 disabled:opacity-40 transition"
                  >
                    <ChevronLeft className="h-3 w-3" />
                    <span>Prev</span>
                  </button>
                  <span className="text-[11px] font-mono text-zinc-400">
                    Step {selectedStepIndex + 1} / {steps.length}
                  </span>
                  <button
                    disabled={selectedStepIndex >= steps.length - 1}
                    onClick={() => setSelectedStepIndex((i) => Math.min(steps.length - 1, i + 1))}
                    className="flex items-center space-x-1 rounded border border-zinc-800 bg-zinc-900 px-2.5 py-1 text-[11px] font-mono text-zinc-300 hover:bg-zinc-800 disabled:opacity-40 transition"
                  >
                    <span>Next</span>
                    <ChevronRight className="h-3 w-3" />
                  </button>
                </div>

                {/* Vertical Step Cards */}
                <div className="space-y-2.5 max-h-[600px] overflow-y-auto pr-1">
                  {steps.map((step, idx) => {
                    const isSelected = idx === selectedStepIndex;
                    const Icon = getAgentIcon(step.agent);

                    return (
                      <button
                        key={step.id || idx}
                        onClick={() => setSelectedStepIndex(idx)}
                        className={`w-full text-left rounded-lg border p-3 transition-all ${
                          isSelected
                            ? 'border-cyan-500/60 bg-cyan-500/10 shadow-md shadow-cyan-500/10 ring-1 ring-cyan-500/30'
                            : 'border-zinc-900 bg-zinc-900/30 hover:border-zinc-800 hover:bg-zinc-900/60'
                        }`}
                      >
                        <div className="flex items-center justify-between text-[11px]">
                          <div className="flex items-center space-x-2">
                            <span className="font-mono text-[10px] text-cyan-400 font-bold">
                              #{step.step_number}
                            </span>
                            <Badge
                              variant={
                                step.action_type === 'SELECTED_STRATEGY'
                                  ? 'emerald'
                                  : step.action_type === 'REJECTED_STRATEGY'
                                  ? 'rose'
                                  : step.action_type === 'DECISION'
                                  ? 'cyan'
                                  : 'outline'
                              }
                              className="text-[9px] py-0 px-1.5 uppercase"
                            >
                              {step.action_type}
                            </Badge>
                          </div>
                          <FormattedTime
                            isoTimestamp={step.timestamp}
                            className="font-mono text-[10px] text-zinc-500"
                          />
                        </div>

                        <div className="mt-2 flex items-start space-x-2">
                          <Icon className="h-4 w-4 text-zinc-400 shrink-0 mt-0.5" />
                          <div>
                            <p className="text-xs font-semibold text-zinc-200">{step.agent}</p>
                            <p className="text-[11px] text-zinc-400 line-clamp-2 leading-snug mt-0.5">
                              {step.output_summary || step.reason}
                            </p>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </Card>
            </div>

            {/* Right Column: Detailed Decision Inspector Panel */}
            <div className="lg:col-span-2 space-y-6">
              {currentStep ? (
                <Card glow>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <GitBranch className="h-4 w-4 text-cyan-400" />
                      <span>Step Detail Inspector (#{currentStep.step_number})</span>
                    </CardTitle>
                    <Badge variant="cyan" className="text-[10px]">
                      Confidence: {(currentStep.confidence * 100).toFixed(0)}%
                    </Badge>
                  </CardHeader>

                  <div className="space-y-5 text-xs">
                    {/* Meta Row */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 border-b border-zinc-900 pb-3 text-zinc-400">
                      <div>
                        <span className="text-[10px] font-mono uppercase text-zinc-500 block">Agent</span>
                        <span className="font-semibold text-zinc-200">{currentStep.agent}</span>
                      </div>
                      <div>
                        <span className="text-[10px] font-mono uppercase text-zinc-500 block">Action</span>
                        <span className="font-mono text-cyan-400">{currentStep.action_type}</span>
                      </div>
                      <div>
                        <span className="text-[10px] font-mono uppercase text-zinc-500 block">Duration</span>
                        <span className="font-mono text-zinc-300">
                          {currentStep.duration_ms > 0 ? `${currentStep.duration_ms}ms` : 'Immediate'}
                        </span>
                      </div>
                      <div>
                        <span className="text-[10px] font-mono uppercase text-zinc-500 block">Timestamp</span>
                        <FormattedTime isoTimestamp={currentStep.timestamp} className="font-mono text-zinc-300" />
                      </div>
                    </div>

                    {/* Step Action & Rationale */}
                    <div className="space-y-1">
                      <span className="text-[10px] uppercase font-mono tracking-wider text-zinc-500">
                        Operational Rationale & Reason
                      </span>
                      <p className="text-sm font-medium text-zinc-100 leading-relaxed bg-zinc-900/50 rounded-lg p-3 border border-zinc-800">
                        {currentStep.reason}
                      </p>
                    </div>

                    {/* Output Summary */}
                    {currentStep.output_summary && (
                      <div className="space-y-1">
                        <span className="text-[10px] uppercase font-mono tracking-wider text-zinc-500">
                          Output Summary
                        </span>
                        <p className="text-xs text-zinc-300 leading-relaxed">{currentStep.output_summary}</p>
                      </div>
                    )}

                    {/* Detailed Strategy Inspector (if Decision stage or strategy step selected) */}
                    {(currentStep.action_type === 'DECISION' ||
                      currentStep.action_type === 'SELECTED_STRATEGY' ||
                      currentStep.action_type === 'REJECTED_STRATEGY' ||
                      currentStep.agent === 'DecisionAgent') && (
                      <div className="border-t border-zinc-900 pt-4 space-y-4">
                        <span className="text-[10px] uppercase font-mono tracking-wider text-cyan-400 font-bold block">
                          Strategy Options Breakdown
                        </span>

                        {/* Selected Strategy Card */}
                        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-4 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="flex items-center space-x-2 text-emerald-400 font-bold text-sm">
                              <CheckCircle className="h-4 w-4 shrink-0" />
                              <span>STRATEGY SELECTED ✓</span>
                            </span>
                            <span className="font-mono text-xs font-semibold text-emerald-400">
                              Score: {((decisionStep?.confidence || 0.95) * 100).toFixed(0)}%
                            </span>
                          </div>

                          <h4 className="text-sm font-bold text-zinc-100">
                            {String(selectedStrategy.title || decisionStep?.output_summary || 'Primary Strategy')}
                          </h4>
                          <p className="text-xs text-zinc-300 leading-relaxed">
                            {String(selectedStrategy.description || decisionStep?.reason || 'Optimal strategy selected.')}
                          </p>
                          <p className="text-[11px] text-emerald-300/80 font-mono italic">
                            Rationale: {decisionStep?.reason || 'Highest combined impact/relevance score.'}
                          </p>
                        </div>

                        {/* Rejected Alternatives Section */}
                        {rejectedStrategies.length > 0 && (
                          <div className="space-y-2">
                            <span className="text-[10px] uppercase font-mono tracking-wider text-rose-400 font-semibold block">
                              Rejected Alternatives ({rejectedStrategies.length})
                            </span>

                            {rejectedStrategies.map((rej, idx) => (
                              <div
                                key={idx}
                                className="rounded-lg border border-rose-500/20 bg-rose-500/5 p-3 space-y-1 opacity-90"
                              >
                                <div className="flex items-center justify-between text-zinc-200 font-semibold">
                                  <span className="flex items-center space-x-1.5 text-rose-400">
                                    <XCircle className="h-3.5 w-3.5 shrink-0" />
                                    <span>{String(rej.title || `Alternative #${idx + 1}`)}</span>
                                  </span>
                                  <Badge variant="rose" className="text-[9px]">
                                    REJECTED
                                  </Badge>
                                </div>
                                <p className="text-[11px] text-zinc-400 leading-normal">
                                  Reason: {String(rej.reason || 'Scored lower than selected strategy in weighted domain evaluation.')}
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </Card>
              ) : (
                <Card className="py-12 text-center text-xs text-zinc-500">
                  Select a step from the chronological timeline to inspect its operational details.
                </Card>
              )}
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
