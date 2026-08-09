export type MissionStatusType = 'INITIALIZED' | 'PLANNING' | 'RESEARCHING' | 'CREATING' | 'REVIEWING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export type AgentRoleType = 'Planner' | 'Research' | 'Decision' | 'Creator' | 'Reviewer';

export type AgentNodeStatus = 'idle' | 'active' | 'completed' | 'failed';

export interface AgentNode {
  id: string;
  name: string;
  role: string;
  description: string;
  status: AgentNodeStatus;
  progressPercentage?: number;
  durationMs?: number;
}

export interface FeedEntryItem {
  id: string;
  mission_id: string;
  current_stage: string;
  timestamp: string;
  agent_responsible: string;
  progress_percentage: number;
  summary_of_work: string;
  decision_made: string;
  confidence: number;
  reflection?: string;
  event_type: string;
  message?: string;
  metadata?: Record<string, unknown>;
}

export interface MissionDetail {
  id: string;
  title: string;
  objective: string;
  description: string;
  status: MissionStatusType;
  priority: 'low' | 'medium' | 'high' | 'critical';
  progressPercentage: number;
  startedAt: string;
  completedAt?: string;
  currentStage: string;
  currentAgent: string;
}

export interface DecisionOption {
  id: string;
  title: string;
  score: number;
  status: 'SELECTED' | 'REJECTED' | 'CANDIDATE';
  description: string;
  rationale: string;
}

export interface DecisionSummary {
  missionId: string;
  selectedStrategyTitle: string;
  reasoning: string;
  confidenceScore: number;
  evaluationsCount: number;
  options: DecisionOption[];
}

export interface MemorySummary {
  totalRecords: number;
  insightsCount: number;
  reflectionsCount: number;
  recentLessons: Array<{
    id: string;
    summary: string;
    insight: string;
    confidenceScore: number;
    createdAt: string;
  }>;
}

export interface SystemHealthStatus {
  status: 'ok' | 'degraded' | 'error';
  serviceName: string;
  timestamp: string;
  autonomousWorkerActive: boolean;
  connectionStatus: 'CONNECTED' | 'RECONNECTING' | 'OFFLINE';
}
