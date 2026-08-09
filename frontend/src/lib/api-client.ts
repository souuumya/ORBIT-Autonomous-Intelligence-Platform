import { apiUrl } from '@/lib/env';
import { FeedEntryItem, MissionStatusType } from '@/types/mission-control';

export interface MissionInitPayload {
  mission_title: string;
  mission_objective: string;
  mission_description?: string;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  user_id?: string;
  context?: Record<string, unknown>;
}

export interface MissionInitResponse {
  mission_id: string;
  status: MissionStatusType;
  created_at: string;
  message: string;
}

export interface FeedResponse {
  mission_id: string;
  entries: FeedEntryItem[];
  total_count: number;
}

export interface HealthCheckResponse {
  status: string;
  service?: string;
  timestamp?: string;
}

export interface ReplayStepData {
  id: string;
  mission_id: string;
  step_number: int;
  timestamp: string;
  agent: string;
  action_type: string;
  reason: string;
  confidence: number;
  duration_ms: number;
  output_summary: string;
  metadata: Record<string, unknown>;
}

export interface ReplayTimelineResponse {
  mission_id: string;
  total_steps: number;
  steps: ReplayStepData[];
}

export interface ReflectionReportResponse {
  mission_id: string;
  what_worked_well: string[];
  what_failed: string[];
  why_failed: string[];
  best_performing_strategy: string;
  deprecated_strategies: string[];
  key_takeaways: string[];
  decision_confidence: number;
  lessons_learned: string[];
  improvement_suggestions: string[];
  performance_score: number;
  created_at: string;
}

export interface MemoryRecordData {
  id: string;
  mission_id: string | null;
  memory_type: string;
  summary: string;
  insight: string;
  confidence_score: number;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface MemoryRetrievalData {
  target_mission_id: string;
  retrievals: Array<{
    id: string;
    summary: string;
    insight: string;
    confidence_score: number;
    created_at: string;
  }>;
  available_prior_experiences: Array<{
    id: string;
    mission_id: string | null;
    memory_type: string;
    summary: string;
    insight: string;
    confidence_score: number;
    created_at: string;
  }>;
}

type int = number;


class ApiClient {
  private get baseUrl(): string {
    return apiUrl.replace(/\/+$/, '');
  }

  async checkHealth(): Promise<HealthCheckResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        cache: 'no-store',
      });
      if (!response.ok) {
        throw new Error(`Health check failed with status ${response.status}`);
      }
      return await response.json();
    } catch {
      try {
        const response = await fetch(`${this.baseUrl}/api/health`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          cache: 'no-store',
        });
        if (response.ok) {
          return await response.json();
        }
      } catch {
        // Fallback error
      }
      throw new Error('Backend health check unavailable');
    }
  }

  async initMission(payload: MissionInitPayload): Promise<MissionInitResponse> {
    const response = await fetch(`${this.baseUrl}/api/agent/init`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        mission_title: payload.mission_title.trim(),
        mission_objective: payload.mission_objective.trim(),
        mission_description: payload.mission_description?.trim() || '',
        priority: payload.priority || 'medium',
        user_id: payload.user_id || 'user-1',
        context: payload.context || {},
      }),
    });

    if (!response.ok) {
      let errorMessage = `Initialization failed with HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson.detail) {
          if (typeof errJson.detail === 'string') {
            errorMessage = errJson.detail;
          } else if (Array.isArray(errJson.detail)) {
            errorMessage = errJson.detail.map((e: { msg?: string }) => e.msg || 'Validation error').join(', ');
          }
        } else if (errJson.message) {
          errorMessage = errJson.message;
        }
      } catch {
        // Non-JSON response
      }
      throw new Error(errorMessage);
    }

    return await response.json();
  }

  async getMissionFeed(missionId: string, limit: number = 50, offset: number = 0): Promise<FeedResponse> {
    if (!missionId) {
      throw new Error('mission_id is required');
    }

    const url = new URL(`${this.baseUrl}/api/agent/feed`);
    url.searchParams.append('mission_id', missionId);
    url.searchParams.append('limit', limit.toString());
    url.searchParams.append('offset', offset.toString());

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store',
    });

    if (!response.ok) {
      let errorMessage = `Failed to fetch feed with HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson.detail) {
          errorMessage = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        } else if (errJson.message) {
          errorMessage = errJson.message;
        }
      } catch {
        // Ignore parse error
      }
      throw new Error(errorMessage);
    }

    return await response.json();
  }

  async getMissionReplay(missionId: string): Promise<ReplayTimelineResponse | null> {
    if (!missionId) return null;
    try {
      const url = new URL(`${this.baseUrl}/api/agent/replay`);
      url.searchParams.append('mission_id', missionId);
      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        cache: 'no-store',
      });
      if (!response.ok) return null;
      return await response.json();
    } catch {
      return null;
    }
  }

  async getMissionReflection(missionId: string): Promise<ReflectionReportResponse | null> {
    if (!missionId) return null;
    try {
      const url = new URL(`${this.baseUrl}/api/agent/reflection`);
      url.searchParams.append('mission_id', missionId);
      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        cache: 'no-store',
      });
      if (!response.ok) return null;
      return await response.json();
    } catch {
      return null;
    }
  }

  async listMissions(status?: string, limit: number = 50, offset: number = 0): Promise<{
    missions: Array<{
      id: string;
      title: string;
      objective: string;
      description: string;
      status: MissionStatusType;
      priority: 'low' | 'medium' | 'high' | 'critical';
      created_at: string;
      updated_at: string;
    }>;
    total_count: number;
  }> {
    try {
      const url = new URL(`${this.baseUrl}/api/agent/missions`);
      if (status) url.searchParams.append('status', status);
      url.searchParams.append('limit', limit.toString());
      url.searchParams.append('offset', offset.toString());

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        cache: 'no-store',
      });

      if (!response.ok) return { missions: [], total_count: 0 };
      return await response.json();
    } catch {
      return { missions: [], total_count: 0 };
    }
  }


  async getMemories(params?: {
    missionId?: string;
    memoryType?: string;
    queryText?: string;
    limit?: number;
  }): Promise<{ memories: MemoryRecordData[]; total_count: number }> {
    try {
      const url = new URL(`${this.baseUrl}/api/agent/memories`);
      if (params?.missionId) url.searchParams.append('mission_id', params.missionId);
      if (params?.memoryType) url.searchParams.append('memory_type', params.memoryType);
      if (params?.queryText) url.searchParams.append('query_text', params.queryText);
      url.searchParams.append('limit', (params?.limit || 50).toString());

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        cache: 'no-store',
      });

      if (!response.ok) return { memories: [], total_count: 0 };
      return await response.json();
    } catch {
      return { memories: [], total_count: 0 };
    }
  }

  async getMemoryRetrieval(missionId: string): Promise<MemoryRetrievalData | null> {
    if (!missionId) return null;
    try {
      const url = new URL(`${this.baseUrl}/api/agent/memory/retrieval`);
      url.searchParams.append('mission_id', missionId);

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        cache: 'no-store',
      });

      if (!response.ok) return null;
      return await response.json();
    } catch {
      return null;
    }
  }
}

export const apiClient = new ApiClient();


