import { describe, it, afterEach } from 'node:test';
import assert from 'node:assert';
import { apiClient } from '../lib/api-client';

const originalFetch = global.fetch;

function mockFetch(handler: (url: string, init?: RequestInit) => Promise<{ ok: boolean; status: number; json: () => Promise<any> }>) {
  global.fetch = (async (url: string, init?: RequestInit) => {
    return handler(url, init);
  }) as unknown as typeof fetch;
}

describe('Phase 5 — Memory & Learning Experience Verification', () => {
  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('Fetches long-term memory records from GET /api/agent/memories', async () => {
    let capturedUrl = '';
    let capturedMethod = '';

    mockFetch(async (url, init) => {
      capturedUrl = url;
      capturedMethod = init?.method || 'GET';
      return {
        ok: true,
        status: 200,
        json: async () => ({
          memories: [
            {
              id: 'mem-101',
              mission_id: 'm-001',
              memory_type: 'mission_reflection',
              summary: 'Mission Reflection for m-001 (Score: 0.96)',
              insight: '{"performance_score": 0.96, "best_performing_strategy": "Strategy A"}',
              confidence_score: 0.96,
              tags: ['mission_reflection', 'm-001'],
              created_at: '2026-08-08T08:00:00Z',
              updated_at: '2026-08-08T08:00:00Z',
            },
            {
              id: 'mem-102',
              mission_id: 'm-001',
              memory_type: 'lesson_learned',
              summary: 'Successful execution of mission: EV Charging',
              insight: 'Domain research briefs directly improve decision confidence (0.94).',
              confidence_score: 0.95,
              tags: ['success', 'ev_charging'],
              created_at: '2026-08-08T08:00:05Z',
              updated_at: '2026-08-08T08:00:05Z',
            },
          ],
          total_count: 2,
        }),
      };
    });

    const res = await apiClient.getMemories({ limit: 10 });

    assert.ok(capturedUrl.includes('/api/agent/memories'));
    assert.strictEqual(capturedMethod, 'GET');
    assert.strictEqual(res.total_count, 2);
    assert.strictEqual(res.memories[0].memory_type, 'mission_reflection');
    assert.strictEqual(res.memories[1].memory_type, 'lesson_learned');
  });

  it('Supports filtering memories by memoryType, missionId, and queryText', async () => {
    let capturedUrl = '';

    mockFetch(async (url) => {
      capturedUrl = url;
      return {
        ok: true,
        status: 200,
        json: async () => ({
          memories: [
            {
              id: 'mem-103',
              mission_id: 'm-002',
              memory_type: 'experience_retrieval',
              summary: 'Retrieved prior experience from 1 previous mission(s)',
              insight: 'Applied prior lesson to AI Education Platform',
              confidence_score: 0.95,
              tags: ['experience_retrieval', 'm-002'],
              created_at: '2026-08-08T08:10:00Z',
              updated_at: '2026-08-08T08:10:00Z',
            },
          ],
          total_count: 1,
        }),
      };
    });

    const res = await apiClient.getMemories({
      memoryType: 'experience_retrieval',
      missionId: 'm-002',
      queryText: 'education',
    });

    assert.ok(capturedUrl.includes('memory_type=experience_retrieval'));
    assert.ok(capturedUrl.includes('mission_id=m-002'));
    assert.ok(capturedUrl.includes('query_text=education'));
    assert.strictEqual(res.memories.length, 1);
    assert.strictEqual(res.memories[0].memory_type, 'experience_retrieval');
  });

  it('Fetches cross-mission experience retrieval data from GET /api/agent/memory/retrieval', async () => {
    let capturedUrl = '';

    mockFetch(async (url) => {
      capturedUrl = url;
      return {
        ok: true,
        status: 200,
        json: async () => ({
          target_mission_id: 'm-002',
          retrievals: [
            {
              id: 'mem-103',
              summary: 'Retrieved prior experience from 1 previous mission(s)',
              insight: 'Applied prior lesson to AI Education Platform',
              confidence_score: 0.95,
              created_at: '2026-08-08T08:10:00Z',
            },
          ],
          available_prior_experiences: [
            {
              id: 'mem-101',
              mission_id: 'm-001',
              memory_type: 'mission_reflection',
              summary: 'Mission Reflection for m-001',
              insight: 'Research briefs improve decision confidence',
              confidence_score: 0.96,
              created_at: '2026-08-08T08:00:00Z',
            },
          ],
        }),
      };
    });

    const data = await apiClient.getMemoryRetrieval('m-002');

    assert.ok(capturedUrl.includes('/api/agent/memory/retrieval'));
    assert.ok(capturedUrl.includes('mission_id=m-002'));
    assert.strictEqual(data?.target_mission_id, 'm-002');
    assert.strictEqual(data?.retrievals.length, 1);
    assert.strictEqual(data?.available_prior_experiences.length, 1);
  });

  it('Handles empty memory states and backend errors gracefully', async () => {
    mockFetch(async () => ({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Internal Server Error' }),
    }));

    const memRes = await apiClient.getMemories();
    assert.deepStrictEqual(memRes, { memories: [], total_count: 0 });

    const retRes = await apiClient.getMemoryRetrieval('invalid-id');
    assert.strictEqual(retRes, null);
  });

  it('Guarantees read-only behavior: Memory operations NEVER issue POST /api/agent/init or mutations', async () => {
    const issuedMethods: string[] = [];

    mockFetch(async (url, init) => {
      issuedMethods.push(init?.method || 'GET');
      return {
        ok: true,
        status: 200,
        json: async () => ({ memories: [], total_count: 0 }),
      };
    });

    await apiClient.getMemories();
    await apiClient.getMemoryRetrieval('m-test');

    assert.ok(issuedMethods.every((m) => m === 'GET'));
    assert.strictEqual(issuedMethods.includes('POST' as any), false);
  });
});
