'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { AppShell } from '@/components/shell';
import {
  Brain,
  Search,
  Filter,
  Layers,
  Sparkles,
  GitBranch,
  BookOpen,
  ArrowRight,
  Database,
  Award,
  Clock,
  Tag,
  Share2,
} from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FormattedTime } from '@/components/ui/formatted-time';
import { ErrorBanner } from '@/components/ui/error-banner';
import {
  apiClient,
  MemoryRecordData,
  MemoryRetrievalData,
} from '@/lib/api-client';
import { motion, AnimatePresence } from 'framer-motion';

interface MissionOption {
  id: string;
  title: string;
  status: string;
}

export function MemoryLearningView() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const urlMissionId = searchParams.get('mission_id');

  const [memories, setMemories] = useState<MemoryRecordData[]>([]);
  const [missions, setMissions] = useState<MissionOption[]>([]);
  const [selectedMemory, setSelectedMemory] = useState<MemoryRecordData | null>(null);
  const [selectedMissionId, setSelectedMissionId] = useState<string | null>(urlMissionId);
  const [retrievalData, setRetrievalData] = useState<MemoryRetrievalData | null>(null);

  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filterType, setFilterType] = useState<string>('all');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'memories' | 'retrieval' | 'timeline'>('memories');

  // Load initial data (missions & long-term memories)
  const loadMemoryData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [memRes, missRes] = await Promise.all([
        apiClient.getMemories({
          memoryType: filterType !== 'all' ? filterType : undefined,
          queryText: searchQuery.trim() || undefined,
          missionId: selectedMissionId || undefined,
        }),
        apiClient.listMissions(undefined, 50, 0),
      ]);

      setMemories(memRes.memories || []);
      setMissions(missRes.missions || []);

      if (memRes.memories && memRes.memories.length > 0 && !selectedMemory) {
        setSelectedMemory(memRes.memories[0]);
      }

      if (selectedMissionId) {
        const retRes = await apiClient.getMemoryRetrieval(selectedMissionId);
        setRetrievalData(retRes);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load long-term memories.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [filterType, searchQuery, selectedMissionId, selectedMemory]);

  useEffect(() => {
    loadMemoryData();
  }, [loadMemoryData]);

  // Handle mission selection change & sync query string
  const handleMissionSelect = (id: string) => {
    const nextId = id === 'all' ? null : id;
    setSelectedMissionId(nextId);
    const params = new URLSearchParams(window.location.search);
    if (nextId) {
      params.set('mission_id', nextId);
    } else {
      params.delete('mission_id');
    }
    router.replace(`/memory?${params.toString()}`, { scroll: false });
  };

  // Metrics derived from real backend data
  const totalMemories = memories.length;
  const contributingMissionsCount = new Set(memories.map((m) => m.mission_id).filter(Boolean)).size;
  const reflectionCount = memories.filter((m) => m.memory_type === 'mission_reflection').length;
  const retrievalCount = memories.filter((m) => m.memory_type === 'experience_retrieval').length;
  const avgConfidence = totalMemories > 0
    ? (memories.reduce((acc, m) => acc + (m.confidence_score || 0), 0) / totalMemories) * 100
    : 0;

  const formatMemoryTypeLabel = (type: string) => {
    switch (type) {
      case 'mission_reflection':
        return 'Reflection Memory';
      case 'lesson_learned':
        return 'Long-Term Lesson';
      case 'experience_retrieval':
        return 'Cross-Mission Retrieval';
      case 'insight':
        return 'Domain Insight';
      case 'working_memory':
        return 'Working Memory';
      default:
        return type.replace(/_/g, ' ');
    }
  };

  const getBadgeVariant = (type: string) => {
    switch (type) {
      case 'mission_reflection':
        return 'cyan';
      case 'lesson_learned':
        return 'emerald';
      case 'experience_retrieval':
        return 'amber';
      default:
        return 'outline';
    }
  };

  return (
    <AppShell currentMissionStatus="INITIALIZED">
      {/* Top Header & Navigation */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-900 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-100 sm:text-2xl flex items-center space-x-2">
            <Brain className="h-6 w-6 text-cyan-400" />
            <span>Long-Term Memory & Learning Engine</span>
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Cross-mission knowledge persistence, experience retrieval, and continuous optimization history
          </p>
        </div>

        {/* View Mode Tabs */}
        <div className="flex items-center space-x-1.5 rounded-lg border border-zinc-800 bg-zinc-900/60 p-1 text-xs">
          <button
            onClick={() => setActiveTab('memories')}
            className={`rounded-md px-3 py-1.5 font-medium transition ${
              activeTab === 'memories'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Memories ({totalMemories})
          </button>
          <button
            onClick={() => setActiveTab('retrieval')}
            className={`rounded-md px-3 py-1.5 font-medium transition ${
              activeTab === 'retrieval'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Cross-Mission Retrieval
          </button>
          <button
            onClick={() => setActiveTab('timeline')}
            className={`rounded-md px-3 py-1.5 font-medium transition ${
              activeTab === 'timeline'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Learning Lifecycle
          </button>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      {/* Metrics Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <Card className="p-3.5 space-y-1 bg-zinc-950/60">
          <span className="text-[10px] font-mono uppercase text-zinc-500 flex items-center space-x-1">
            <Database className="h-3 w-3 text-cyan-400" />
            <span>Memories Stored</span>
          </span>
          <p className="text-xl font-bold font-mono text-zinc-100">{totalMemories}</p>
        </Card>

        <Card className="p-3.5 space-y-1 bg-zinc-950/60">
          <span className="text-[10px] font-mono uppercase text-zinc-500 flex items-center space-x-1">
            <Layers className="h-3 w-3 text-emerald-400" />
            <span>Source Missions</span>
          </span>
          <p className="text-xl font-bold font-mono text-emerald-400">{contributingMissionsCount}</p>
        </Card>

        <Card className="p-3.5 space-y-1 bg-zinc-950/60">
          <span className="text-[10px] font-mono uppercase text-zinc-500 flex items-center space-x-1">
            <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
            <span>Reflections</span>
          </span>
          <p className="text-xl font-bold font-mono text-cyan-400">{reflectionCount}</p>
        </Card>

        <Card className="p-3.5 space-y-1 bg-zinc-950/60">
          <span className="text-[10px] font-mono uppercase text-zinc-500 flex items-center space-x-1">
            <Share2 className="h-3.5 w-3.5 text-amber-400" />
            <span>Retrievals</span>
          </span>
          <p className="text-xl font-bold font-mono text-amber-400">{retrievalCount}</p>
        </Card>

        <Card className="p-3.5 space-y-1 bg-zinc-950/60 col-span-2 sm:col-span-1">
          <span className="text-[10px] font-mono uppercase text-zinc-500 flex items-center space-x-1">
            <Award className="h-3.5 w-3.5 text-cyan-400" />
            <span>Avg Confidence</span>
          </span>
          <p className="text-xl font-bold font-mono text-zinc-100">{avgConfidence.toFixed(0)}%</p>
        </Card>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 border-b border-zinc-900 pb-3">
        {/* Search input */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-zinc-500" />
          <input
            type="text"
            placeholder="Search memory insights & lessons..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-zinc-800 bg-zinc-900 pl-9 pr-3 py-1.5 text-xs text-zinc-100 placeholder-zinc-500 focus:border-cyan-500 focus:outline-none transition"
          />
        </div>

        {/* Filters */}
        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-1 text-zinc-400">
            <Filter className="h-3.5 w-3.5 text-cyan-400" />
            <span>Type:</span>
          </div>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none transition"
          >
            <option value="all">All Memory Types</option>
            <option value="mission_reflection">Reflection Memory</option>
            <option value="lesson_learned">Long-Term Lesson</option>
            <option value="experience_retrieval">Experience Retrieval</option>
            <option value="insight">Domain Insight</option>
          </select>

          <select
            value={selectedMissionId || 'all'}
            onChange={(e) => handleMissionSelect(e.target.value)}
            className="rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none transition max-w-xs"
          >
            <option value="all">All Source Missions</option>
            {missions.map((m) => (
              <option key={m.id} value={m.id}>
                {m.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Tab Content */}
      {activeTab === 'memories' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Memory List */}
          <div className="lg:col-span-1 space-y-3">
            {memories.length === 0 && !isLoading ? (
              <Card className="py-12 text-center text-xs space-y-2 border-dashed border-zinc-800">
                <Brain className="h-8 w-8 text-zinc-600 mx-auto" />
                <p className="font-semibold text-zinc-300">No Learned Experience Yet</p>
                <p className="text-zinc-500 max-w-xs mx-auto text-[11px]">
                  Initialize and complete autonomous missions to generate persisted long-term memory records.
                </p>
              </Card>
            ) : (
              <div className="space-y-2.5 max-h-[650px] overflow-y-auto pr-1">
                {memories.map((mem) => {
                  const isSelected = selectedMemory?.id === mem.id;
                  const badgeVariant = getBadgeVariant(mem.memory_type);

                  return (
                    <button
                      key={mem.id}
                      onClick={() => setSelectedMemory(mem)}
                      className={`w-full text-left rounded-lg border p-3.5 transition-all ${
                        isSelected
                          ? 'border-cyan-500/60 bg-cyan-500/10 shadow-md shadow-cyan-500/10 ring-1 ring-cyan-500/30'
                          : 'border-zinc-900 bg-zinc-900/30 hover:border-zinc-800 hover:bg-zinc-900/60'
                      }`}
                    >
                      <div className="flex items-center justify-between text-[11px]">
                        <Badge variant={badgeVariant} className="text-[9px] uppercase px-1.5 py-0">
                          {formatMemoryTypeLabel(mem.memory_type)}
                        </Badge>
                        <FormattedTime
                          isoTimestamp={mem.created_at}
                          className="font-mono text-[10px] text-zinc-500"
                        />
                      </div>

                      <h3 className="text-xs font-semibold text-zinc-200 mt-2 line-clamp-1">
                        {mem.summary}
                      </h3>
                      <p className="text-[11px] text-zinc-400 line-clamp-2 mt-1 leading-snug">
                        {mem.insight}
                      </p>

                      <div className="mt-2.5 flex items-center justify-between text-[10px] font-mono text-zinc-500">
                        <span>Score: {(mem.confidence_score * 100).toFixed(0)}%</span>
                        {mem.mission_id && (
                          <span className="text-cyan-400/80 truncate max-w-[120px]">
                            Mission: {mem.mission_id.substring(0, 8)}...
                          </span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right Column: Detailed Memory Inspector */}
          <div className="lg:col-span-2 space-y-6">
            {selectedMemory ? (
              <Card glow className="p-6 space-y-5">
                <CardHeader className="p-0 border-b border-zinc-900 pb-4">
                  <div className="flex items-center justify-between">
                    <Badge variant={getBadgeVariant(selectedMemory.memory_type)}>
                      {formatMemoryTypeLabel(selectedMemory.memory_type)}
                    </Badge>
                    <span className="font-mono text-xs text-emerald-400 font-semibold">
                      Confidence: {(selectedMemory.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <CardTitle className="text-lg font-bold text-zinc-100 mt-2">
                    {selectedMemory.summary}
                  </CardTitle>
                </CardHeader>

                <div className="space-y-4 text-xs">
                  {/* Meta Metadata Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 border-b border-zinc-900 pb-3 text-zinc-400">
                    <div>
                      <span className="text-[10px] font-mono uppercase text-zinc-500 block">Memory ID</span>
                      <span className="font-mono text-zinc-300 text-[11px] truncate block">
                        {selectedMemory.id}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase text-zinc-500 block">Source Mission</span>
                      <span className="font-mono text-cyan-400 text-[11px] truncate block">
                        {selectedMemory.mission_id || 'System Core'}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase text-zinc-500 block">Created At</span>
                      <FormattedTime isoTimestamp={selectedMemory.created_at} className="font-mono text-zinc-300" />
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase text-zinc-500 block">Type</span>
                      <span className="font-mono text-zinc-300">{selectedMemory.memory_type}</span>
                    </div>
                  </div>

                  {/* Insight / Lessons Content */}
                  <div className="space-y-1.5">
                    <span className="text-[10px] uppercase font-mono tracking-wider text-cyan-400 font-semibold block">
                      Persisted Memory Insight & Knowledge Content
                    </span>
                    <div className="rounded-lg border border-zinc-800 bg-zinc-950/80 p-4 text-xs font-mono text-zinc-200 leading-relaxed overflow-x-auto">
                      {selectedMemory.insight.startsWith('{') ? (
                        <pre className="whitespace-pre-wrap font-mono text-[11px]">
                          {JSON.stringify(JSON.parse(selectedMemory.insight), null, 2)}
                        </pre>
                      ) : (
                        <p className="text-zinc-200 font-sans text-xs leading-relaxed">
                          {selectedMemory.insight}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Tags */}
                  {selectedMemory.tags && selectedMemory.tags.length > 0 && (
                    <div className="space-y-1.5 pt-2">
                      <span className="text-[10px] uppercase font-mono tracking-wider text-zinc-500 flex items-center space-x-1">
                        <Tag className="h-3 w-3 text-cyan-400" />
                        <span>Associated Knowledge Tags</span>
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedMemory.tags.map((tag, idx) => (
                          <span
                            key={idx}
                            className="rounded bg-zinc-900 border border-zinc-800 px-2 py-0.5 text-[10px] font-mono text-cyan-400"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            ) : (
              <Card className="py-16 text-center text-xs text-zinc-500">
                Select a long-term memory record from the list to inspect its knowledge payload.
              </Card>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Cross-Mission Experience Retrieval Visualizer */}
      {activeTab === 'retrieval' && (
        <Card glow className="p-6 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-zinc-900 pb-4 gap-4">
            <div>
              <h2 className="text-base font-bold text-zinc-100 flex items-center space-x-2">
                <Share2 className="h-5 w-5 text-amber-400" />
                <span>Cross-Mission Experience Retrieval Flow</span>
              </h2>
              <p className="text-xs text-zinc-400 mt-0.5">
                Demonstrating how prior mission learnings are retrieved to inform decisions in subsequent missions
              </p>
            </div>

            <select
              value={selectedMissionId || ''}
              onChange={(e) => handleMissionSelect(e.target.value)}
              className="rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none transition max-w-xs"
            >
              <option value="">Select Target Mission...</option>
              {missions.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.title}
                </option>
              ))}
            </select>
          </div>

          {/* Flow Diagram */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
            {/* Step A: Prior Mission */}
            <div className="rounded-lg border border-cyan-500/30 bg-zinc-900/40 p-4 space-y-2">
              <span className="text-[10px] font-mono uppercase text-cyan-400 font-bold block">
                1. Prior Completed Mission
              </span>
              <p className="font-semibold text-zinc-200 text-xs">
                Mission A Execution
              </p>
              <p className="text-[11px] text-zinc-400 leading-snug">
                Completed workflow & generated post-review reflection.
              </p>
            </div>

            {/* Step B: Memory Persisted */}
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-4 space-y-2">
              <span className="text-[10px] font-mono uppercase text-emerald-400 font-bold block">
                2. Stored Memory
              </span>
              <p className="font-semibold text-emerald-300 text-xs">
                Long-Term Knowledge Record
              </p>
              <p className="text-[11px] text-zinc-400 leading-snug">
                Reflection & lesson stored in `MemoryRecordModel`.
              </p>
            </div>

            {/* Step C: Experience Retrieval */}
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4 space-y-2">
              <span className="text-[10px] font-mono uppercase text-amber-400 font-bold block">
                3. Memory Retrieval
              </span>
              <p className="font-semibold text-amber-300 text-xs">
                ResearchAgent Context Query
              </p>
              <p className="text-[11px] text-zinc-400 leading-snug">
                `MemoryEngine.retrieve_relevant_memories()` finds prior lesson.
              </p>
            </div>

            {/* Step D: Informed Decision */}
            <div className="rounded-lg border border-cyan-500/40 bg-cyan-500/10 p-4 space-y-2">
              <span className="text-[10px] font-mono uppercase text-cyan-400 font-bold block">
                4. Informed Decision
              </span>
              <p className="font-semibold text-cyan-300 text-xs">
                DecisionAgent Selection
              </p>
              <p className="text-[11px] text-zinc-400 leading-snug">
                Decision candidate scoring incorporates prior experience.
              </p>
            </div>
          </div>

          {/* Real Retrieved Memories Panel for Selected Mission */}
          {selectedMissionId ? (
            <div className="border-t border-zinc-900 pt-4 space-y-3">
              <h3 className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">
                Persisted Experience Retrieval Data for Mission ({selectedMissionId.substring(0, 8)}...)
              </h3>

              {retrievalData?.retrievals && retrievalData.retrievals.length > 0 ? (
                <div className="space-y-2">
                  {retrievalData.retrievals.map((r) => (
                    <div
                      key={r.id}
                      className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-3.5 space-y-1"
                    >
                      <div className="flex items-center justify-between text-xs font-semibold text-amber-300">
                        <span>{r.summary}</span>
                        <span className="font-mono text-[10px] text-zinc-500">
                          Score: {(r.confidence_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-xs text-zinc-300 font-mono">{r.insight}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-lg border border-zinc-900 bg-zinc-950 p-4 text-xs text-zinc-400 space-y-1">
                  <p className="font-semibold text-zinc-300">
                    Experience Retrieval Recorded
                  </p>
                  <p className="text-[11px] text-zinc-500">
                    Prior long-term memories in DB are queried during `ResearchAgent` stage execution and attached to research briefs.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-zinc-500 text-center py-6">
              Select a target mission above to inspect its retrieved experience records.
            </p>
          )}
        </Card>
      )}

      {/* Tab 3: Learning Lifecycle Overview */}
      {activeTab === 'timeline' && (
        <Card glow className="p-6 space-y-6">
          <div className="border-b border-zinc-900 pb-3">
            <h2 className="text-base font-bold text-zinc-100 flex items-center space-x-2">
              <BookOpen className="h-5 w-5 text-cyan-400" />
              <span>Autonomous Learning Lifecycle</span>
            </h2>
            <p className="text-xs text-zinc-400 mt-0.5">
              How autonomous missions convert execution outcomes into persistent knowledge
            </p>
          </div>

          <div className="space-y-4">
            <div className="flex items-start space-x-4">
              <div className="rounded-full bg-cyan-500/20 p-2 text-cyan-400 border border-cyan-500/30 font-mono text-xs font-bold">
                01
              </div>
              <div className="space-y-1 text-xs">
                <h3 className="font-bold text-zinc-200">Mission Execution & Decision Auditing</h3>
                <p className="text-zinc-400 leading-relaxed">
                  Agents execute milestones, formulate candidate strategies, and evaluate risk-weighted scores.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="rounded-full bg-emerald-500/20 p-2 text-emerald-400 border border-emerald-500/30 font-mono text-xs font-bold">
                02
              </div>
              <div className="space-y-1 text-xs">
                <h3 className="font-bold text-zinc-200">Reviewer Quality Evaluation & Self-Correction</h3>
                <p className="text-zinc-400 leading-relaxed">
                  ReviewerAgent scores deliverable quality and triggers revision loops if scores fall below threshold.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="rounded-full bg-amber-500/20 p-2 text-amber-400 border border-amber-500/30 font-mono text-xs font-bold">
                03
              </div>
              <div className="space-y-1 text-xs">
                <h3 className="font-bold text-zinc-200">Reflection Engine Post-Review Synthesis</h3>
                <p className="text-zinc-400 leading-relaxed">
                  ReflectionEngine computes performance scores, identifies lessons learned, and highlights top-performing strategies.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="rounded-full bg-cyan-500/20 p-2 text-cyan-400 border border-cyan-500/30 font-mono text-xs font-bold">
                04
              </div>
              <div className="space-y-1 text-xs">
                <h3 className="font-bold text-zinc-200">MemoryEngine Long-Term Database Persistence</h3>
                <p className="text-zinc-400 leading-relaxed">
                  Lessons learned and reflection reports are stored in `MemoryRecordModel` database records for cross-mission reuse.
                </p>
              </div>
            </div>
          </div>
        </Card>
      )}
    </AppShell>
  );
}
