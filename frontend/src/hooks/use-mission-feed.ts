'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { apiClient, MissionInitPayload, ReflectionReportResponse, ReplayTimelineResponse } from '@/lib/api-client';
import {
  AgentNode,
  DecisionOption,
  DecisionSummary,
  FeedEntryItem,
  MemorySummary,
  MissionDetail,
  MissionStatusType,
  SystemHealthStatus,
} from '@/types/mission-control';

const BASE_AGENT_NODES: Omit<AgentNode, 'status' | 'durationMs' | 'progressPercentage'>[] = [
  { id: 'node-mission', name: 'Mission Core', role: 'Orchestrator', description: 'System initialization & lifecycle manager' },
  { id: 'node-planner', name: 'Planner Agent', role: 'Planner', description: 'Decomposes objective into milestones & task graph' },
  { id: 'node-research', name: 'Research Agent', role: 'Research', description: 'Gathers context & competitive domain evidence' },
  { id: 'node-decision', name: 'Decision Agent', role: 'Decision', description: 'Scores candidate strategies & selects optimal path' },
  { id: 'node-creator', name: 'Creator Agent', role: 'Creator', description: 'Synthesizes primary deliverable content artifacts' },
  { id: 'node-reviewer', name: 'Reviewer Agent', role: 'Reviewer', description: 'Quality verification & self-correction evaluation' },
  { id: 'node-memory', name: 'Memory & Reflection', role: 'Engine', description: 'Post-mission self-review & long-term memory update' },
];

const INITIAL_SYSTEM_STATUS: SystemHealthStatus = {
  status: 'ok',
  serviceName: 'Autonomous Intelligence Core',
  timestamp: new Date().toISOString(),
  autonomousWorkerActive: true,
  connectionStatus: 'CONNECTED',
};

const LOCAL_STORAGE_KEY_ID = 'orbit_active_mission_id';
const LOCAL_STORAGE_KEY_META = 'orbit_active_mission_meta';

export function useMissionFeed(initialMissionId: string | null = null) {
  const [activeMissionId, setActiveMissionId] = useState<string | null>(initialMissionId);
  const [mission, setMission] = useState<MissionDetail | null>(null);
  const [feedItems, setFeedItems] = useState<FeedEntryItem[]>([]);
  const [agentNodes, setAgentNodes] = useState<AgentNode[]>(
    BASE_AGENT_NODES.map((n) => ({ ...n, status: 'idle' as const }))
  );
  const [decisionSummary, setDecisionSummary] = useState<DecisionSummary | null>(null);
  const [memorySummary, setMemorySummary] = useState<MemorySummary | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemHealthStatus>(INITIAL_SYSTEM_STATUS);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isInitializing, setIsInitializing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const initInFlightRef = useRef<boolean>(false);
  const pollingTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Restore active mission from localStorage on mount
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const storedId = localStorage.getItem(LOCAL_STORAGE_KEY_ID);
    const storedMetaJson = localStorage.getItem(LOCAL_STORAGE_KEY_META);

    if (storedId) {
      setActiveMissionId(storedId);
      if (storedMetaJson) {
        try {
          const meta = JSON.parse(storedMetaJson);
          setMission({
            id: storedId,
            title: meta.title || `Mission ${storedId.slice(0, 8)}`,
            objective: meta.objective || 'Autonomous execution pipeline',
            description: meta.description || '',
            status: 'INITIALIZED',
            priority: meta.priority || 'medium',
            progressPercentage: 0,
            startedAt: meta.startedAt || new Date().toISOString(),
            currentStage: 'INITIALIZED',
            currentAgent: 'System',
          });
        } catch {
          // Ignore invalid cached meta
        }
      }
    }
  }, []);

  // Derive status from feed entries
  const deriveMissionStatus = (entries: FeedEntryItem[], currentStatus: MissionStatusType): MissionStatusType => {
    if (entries.length === 0) return currentStatus;

    // Check if completion, failure, or cancellation occurred anywhere in the feed
    for (let i = entries.length - 1; i >= 0; i--) {
      const entry = entries[i];
      const stage = (entry.current_stage || '').toUpperCase();
      const eventType = entry.event_type || '';
      const toState = (entry.metadata?.to_state || '').toString().toUpperCase();

      if (stage.includes('COMPLETED') || eventType === 'MissionCompleted' || toState === 'COMPLETED') {
        return 'COMPLETED';
      }
      if (stage.includes('FAILED') || eventType === 'MissionFailed' || toState === 'FAILED') {
        return 'FAILED';
      }
      if (stage.includes('CANCELLED') || eventType === 'MissionCancelled' || toState === 'CANCELLED') {
        return 'CANCELLED';
      }
    }

    // Determine current active stage from the latest meaningful entry
    for (let i = entries.length - 1; i >= 0; i--) {
      const entry = entries[i];
      const stage = (entry.current_stage || '').toUpperCase();
      const toState = (entry.metadata?.to_state || '').toString().toUpperCase();

      const effectiveStage = stage !== 'INITIALIZED' && stage ? stage : toState;

      if (effectiveStage.includes('REVIEW')) return 'REVIEWING';
      if (effectiveStage.includes('CREAT')) return 'CREATING';
      if (effectiveStage.includes('DECISION')) return 'CREATING';
      if (effectiveStage.includes('RESEARCH')) return 'RESEARCHING';
      if (effectiveStage.includes('PLAN')) return 'PLANNING';
    }

    return 'INITIALIZED';
  };

  // Derive agent nodes state strictly from feed entries and mission status
  const deriveAgentNodes = (entries: FeedEntryItem[], missionStatus: MissionStatusType): AgentNode[] => {
    if (entries.length === 0) {
      return BASE_AGENT_NODES.map((node, idx) => ({
        ...node,
        status: idx === 0 && (missionStatus === 'INITIALIZED' || missionStatus === 'PLANNING') ? 'active' : 'idle',
      }));
    }

    const isFinished = missionStatus === 'COMPLETED';
    const isFailed = missionStatus === 'FAILED';
    const stageOrder = ['orchestrator', 'planner', 'research', 'decision', 'creator', 'reviewer', 'engine'];

    let activeIndex = 0;
    if (isFinished) {
      activeIndex = 6;
    } else {
      for (let i = entries.length - 1; i >= 0; i--) {
        const e = entries[i];
        const resp = (e.agent_responsible || '').toLowerCase();
        const stage = (e.current_stage || '').toLowerCase();
        const toState = (e.metadata?.to_state || '').toString().toLowerCase();
        const combined = `${resp} ${stage} ${toState}`;

        if (combined.includes('reflection') || combined.includes('memory') || combined.includes('completed')) {
          activeIndex = 6;
          break;
        } else if (combined.includes('reviewer') || combined.includes('review')) {
          activeIndex = 5;
          break;
        } else if (combined.includes('creator') || combined.includes('creat')) {
          activeIndex = 4;
          break;
        } else if (combined.includes('decision')) {
          activeIndex = 3;
          break;
        } else if (combined.includes('research')) {
          activeIndex = 2;
          break;
        } else if (combined.includes('planner') || combined.includes('plan')) {
          activeIndex = 1;
          break;
        }
      }
    }

    return BASE_AGENT_NODES.map((node) => {
      const roleLower = node.role.toLowerCase() === 'memory' ? 'engine' : node.role.toLowerCase();
      const myIndex = stageOrder.indexOf(roleLower);

      let status: 'idle' | 'active' | 'completed' | 'failed' = 'idle';

      if (isFinished) {
        status = 'completed';
      } else if (isFailed) {
        if (myIndex < activeIndex) status = 'completed';
        else if (myIndex === activeIndex) status = 'failed';
        else status = 'idle';
      } else {
        if (myIndex < activeIndex) status = 'completed';
        else if (myIndex === activeIndex) status = 'active';
        else status = 'idle';
      }

      let durationMs: number | undefined;
      const matchingEntries = entries.filter((e) => {
        const resp = (e.agent_responsible || '').toLowerCase();
        const stage = (e.current_stage || '').toLowerCase();
        return resp.includes(roleLower) || stage.includes(roleLower);
      });

      if (matchingEntries.length > 1) {
        const first = new Date(matchingEntries[0].timestamp).getTime();
        const last = new Date(matchingEntries[matchingEntries.length - 1].timestamp).getTime();
        if (last > first) {
          durationMs = Math.round(last - first);
        }
      }

      return {
        ...node,
        status,
        durationMs,
      };
    });
  };

  // Derive Decision Summary from replay API or feed entry
  const deriveDecisionSummary = (
    entries: FeedEntryItem[],
    missionId: string,
    replay?: ReplayTimelineResponse | null
  ): DecisionSummary | null => {
    // 1. Try replay API steps first
    if (replay && replay.steps.length > 0) {
      const decisionSteps = replay.steps.filter(
        (s) => s.agent.toLowerCase().includes('decision') || s.action_type.toLowerCase().includes('decision')
      );

      if (decisionSteps.length > 0) {
        const lastStep = decisionSteps[decisionSteps.length - 1];
        const selectedTitle = lastStep.output_summary || lastStep.reason || 'Optimal Strategy Selected';
        const metaOptions = (lastStep.metadata?.options as DecisionOption[]) || [];

        const options: DecisionOption[] = metaOptions.length > 0
          ? metaOptions
          : [
              {
                id: 'opt-selected',
                title: selectedTitle.replace(/^Selected\s*['"]?|['"]?$/gi, ''),
                score: lastStep.confidence || 0.95,
                status: 'SELECTED',
                description: lastStep.reason || 'Selected based on domain evidence and weighted risk analysis.',
                rationale: 'Top candidate score from Decision Agent evaluation.',
              },
            ];

        return {
          missionId,
          selectedStrategyTitle: selectedTitle.replace(/^Selected\s*['"]?|['"]?$/gi, ''),
          reasoning: lastStep.reason || lastStep.output_summary || 'Evaluated candidates against domain brief.',
          confidenceScore: lastStep.confidence || 0.95,
          evaluationsCount: options.length,
          options,
        };
      }
    }

    // 2. Fallback to decision feed entry
    const decisionEntry = entries.find(
      (e) =>
        (e.agent_responsible || '').toLowerCase().includes('decision') ||
        (e.current_stage || '').toLowerCase().includes('decision') ||
        e.event_type === 'DecisionCompleted'
    );

    if (!decisionEntry) return null;

    const selectedTitle = decisionEntry.decision_made || 'Strategy Selected';
    const reasoning = decisionEntry.summary_of_work || 'Evaluated candidate strategies.';
    const confidenceScore = decisionEntry.confidence || 0.95;

    return {
      missionId,
      selectedStrategyTitle: selectedTitle.replace(/^Selected\s*['"]?|['"]?$/gi, ''),
      reasoning,
      confidenceScore,
      evaluationsCount: 1,
      options: [
        {
          id: 'opt-selected',
          title: selectedTitle.replace(/^Selected\s*['"]?|['"]?$/gi, ''),
          score: confidenceScore,
          status: 'SELECTED',
          description: reasoning,
          rationale: 'Validated against research brief.',
        },
      ],
    };
  };

  // Derive Memory Summary from reflection API or feed entries
  const deriveMemorySummary = (
    entries: FeedEntryItem[],
    reflection?: ReflectionReportResponse | null
  ): MemorySummary | null => {
    // 1. Try reflection report first
    if (reflection) {
      const lessons = (reflection.lessons_learned || reflection.key_takeaways || []).map((lesson, idx) => ({
        id: `mem-ref-${idx}`,
        summary: reflection.best_performing_strategy
          ? `Validated Strategy: ${reflection.best_performing_strategy}`
          : `Post-mission insight #${idx + 1}`,
        insight: lesson,
        confidenceScore: reflection.performance_score || reflection.decision_confidence || 0.95,
        createdAt: reflection.created_at || new Date().toISOString(),
      }));

      if (lessons.length > 0) {
        return {
          totalRecords: lessons.length,
          insightsCount: reflection.what_worked_well.length || lessons.length,
          reflectionsCount: lessons.length,
          recentLessons: lessons,
        };
      }
    }

    // 2. Fallback to reflection feed entries
    const reflectionEntries = entries.filter(
      (e) => e.reflection || (e.agent_responsible || '').toLowerCase().includes('reflection')
    );

    if (reflectionEntries.length === 0) return null;

    const lessons = reflectionEntries.map((e, idx) => ({
      id: `mem-${e.id || idx}`,
      summary: e.summary_of_work || 'Post-execution review lesson',
      insight: e.reflection || e.decision_made || 'Autonomous execution completed',
      confidenceScore: e.confidence || 0.95,
      createdAt: e.timestamp,
    }));

    return {
      totalRecords: lessons.length,
      insightsCount: lessons.length,
      reflectionsCount: lessons.length,
      recentLessons: lessons,
    };
  };

  // Health check on mount
  useEffect(() => {
    let isMounted = true;
    apiClient
      .checkHealth()
      .then((res) => {
        if (isMounted) {
          setSystemStatus({
            status: res.status === 'ok' ? 'ok' : 'degraded',
            serviceName: res.service || 'Autonomous Intelligence Core',
            timestamp: res.timestamp || new Date().toISOString(),
            autonomousWorkerActive: true,
            connectionStatus: 'CONNECTED',
          });
        }
      })
      .catch(() => {
        if (isMounted) {
          setSystemStatus((prev) => ({
            ...prev,
            connectionStatus: 'OFFLINE',
          }));
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Poll feed & endpoints
  const fetchFeed = useCallback(async (missionId: string) => {
    try {
      const response = await apiClient.getMissionFeed(missionId, 100, 0);
      setError(null);

      setSystemStatus((prev) => ({
        ...prev,
        connectionStatus: 'CONNECTED',
      }));

      const rawEntries = response.entries || [];
      const seenIds = new Set<string>();
      const uniqueEntries: FeedEntryItem[] = [];

      for (const entry of rawEntries) {
        if (!seenIds.has(entry.id)) {
          seenIds.add(entry.id);
          uniqueEntries.push(entry);
        }
      }

      uniqueEntries.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
      setFeedItems(uniqueEntries);

      const latestEntry = uniqueEntries[uniqueEntries.length - 1];
      const status = deriveMissionStatus(uniqueEntries, 'INITIALIZED');
      const currentStage = latestEntry ? latestEntry.current_stage : 'INITIALIZED';
      const currentAgent = latestEntry ? latestEntry.agent_responsible : 'System';
      const progressPercentage = latestEntry ? latestEntry.progress_percentage : 0;

      setMission((prev) => ({
        id: missionId,
        title: prev?.title || `Mission ${missionId.slice(0, 8)}`,
        objective: prev?.objective || 'Autonomous multi-agent execution pipeline',
        description: prev?.description || '',
        status,
        priority: prev?.priority || 'medium',
        progressPercentage: Math.min(100, Math.max(0, progressPercentage)),
        startedAt: uniqueEntries[0]?.timestamp || prev?.startedAt || new Date().toISOString(),
        completedAt: status === 'COMPLETED' ? latestEntry?.timestamp || new Date().toISOString() : undefined,
        currentStage,
        currentAgent,
      }));

      // Set agent nodes from actual feed entries
      setAgentNodes(deriveAgentNodes(uniqueEntries, status));

      // Fetch Replay / Reflection if stage appropriate
      let replayData: ReplayTimelineResponse | null = null;
      let reflectionData: ReflectionReportResponse | null = null;

      if (uniqueEntries.some((e) => (e.agent_responsible || '').toLowerCase().includes('decision'))) {
        replayData = await apiClient.getMissionReplay(missionId);
      }

      if (status === 'COMPLETED' || uniqueEntries.some((e) => e.reflection)) {
        reflectionData = await apiClient.getMissionReflection(missionId);
      }

      // Update Decision & Memory summaries
      setDecisionSummary(deriveDecisionSummary(uniqueEntries, missionId, replayData));
      setMemorySummary(deriveMemorySummary(uniqueEntries, reflectionData));

      return status;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Feed fetch failed';
      setError(msg);
      setSystemStatus((prev) => ({
        ...prev,
        connectionStatus: 'OFFLINE',
      }));
      return 'FAILED' as MissionStatusType;
    }
  }, []);

  // Polling loop
  useEffect(() => {
    if (!activeMissionId) return;

    let isSubscribed = true;

    const poll = async () => {
      if (!isSubscribed) return;
      setIsLoading(true);
      const status = await fetchFeed(activeMissionId);
      if (isSubscribed) setIsLoading(false);

      if (isSubscribed && status !== 'COMPLETED' && status !== 'FAILED' && status !== 'CANCELLED') {
        pollingTimerRef.current = setTimeout(poll, 1500);
      }
    };

    poll();

    return () => {
      isSubscribed = false;
      if (pollingTimerRef.current) {
        clearTimeout(pollingTimerRef.current);
      }
    };
  }, [activeMissionId, fetchFeed]);

  // Mission Initialization
  const initializeMission = async (payload: MissionInitPayload): Promise<string> => {
    if (initInFlightRef.current) {
      throw new Error('Initialization request already in progress.');
    }

    initInFlightRef.current = true;
    setIsInitializing(true);
    setError(null);

    try {
      const res = await apiClient.initMission(payload);
      const newMissionId = res.mission_id;

      // Save to localStorage for persistence across browser refreshes
      if (typeof window !== 'undefined') {
        localStorage.setItem(LOCAL_STORAGE_KEY_ID, newMissionId);
        localStorage.setItem(
          LOCAL_STORAGE_KEY_META,
          JSON.stringify({
            title: payload.mission_title,
            objective: payload.mission_objective,
            priority: payload.priority || 'medium',
            description: payload.mission_description || '',
            startedAt: res.created_at || new Date().toISOString(),
          })
        );
      }

      setMission({
        id: newMissionId,
        title: payload.mission_title,
        objective: payload.mission_objective,
        description: payload.mission_description || '',
        status: res.status || 'INITIALIZED',
        priority: payload.priority || 'medium',
        progressPercentage: 0,
        startedAt: res.created_at || new Date().toISOString(),
        currentStage: 'INITIALIZED',
        currentAgent: 'System',
      });

      setFeedItems([]);
      setDecisionSummary(null);
      setMemorySummary(null);
      setAgentNodes(BASE_AGENT_NODES.map((n, i) => ({ ...n, status: i === 0 ? 'active' : 'idle' })));
      setActiveMissionId(newMissionId);

      // Trigger immediate initial feed poll
      fetchFeed(newMissionId);

      return newMissionId;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Mission initialization failed';
      setError(msg);
      throw err;
    } finally {
      setIsInitializing(false);
      initInFlightRef.current = false;
    }
  };

  // Reset / Clear Mission action
  const resetMission = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(LOCAL_STORAGE_KEY_ID);
      localStorage.removeItem(LOCAL_STORAGE_KEY_META);
    }
    setActiveMissionId(null);
    setMission(null);
    setFeedItems([]);
    setAgentNodes(BASE_AGENT_NODES.map((n) => ({ ...n, status: 'idle' as const })));
    setDecisionSummary(null);
    setMemorySummary(null);
    setError(null);
  };

  return {
    mission,
    feedItems,
    agentNodes,
    decisionSummary,
    memorySummary,
    systemStatus,
    isLoading,
    isInitializing,
    error,
    activeMissionId,
    initializeMission,
    resetMission,
    refreshFeed: () => (activeMissionId ? fetchFeed(activeMissionId) : null),
  };
}
