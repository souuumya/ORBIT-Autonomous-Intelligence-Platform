import { describe, it, afterEach } from 'node:test';
import assert from 'node:assert';
import { apiClient, MissionInitPayload } from '../lib/api-client';

const originalFetch = global.fetch;

function mockFetch(handler: (url: string, init?: RequestInit) => Promise<{ ok: boolean; status: number; json: () => Promise<any> }>) {
  global.fetch = (async (url: string, init?: RequestInit) => {
    return handler(url, init);
  }) as unknown as typeof fetch;
}

describe('Phase 3B - API Client & Mission Feed Verification', () => {
  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('Mission initialization calls POST /api/agent/init with formatted body', async () => {
    let capturedUrl = '';
    let capturedMethod = '';
    let capturedBody: any = null;

    mockFetch(async (url, init) => {
      capturedUrl = url;
      capturedMethod = init?.method || '';
      capturedBody = JSON.parse((init?.body as string) || '{}');
      return {
        ok: true,
        status: 200,
        json: async () => ({
          mission_id: 'test-mission-123',
          status: 'INITIALIZED',
          created_at: '2026-08-08T08:00:00Z',
          message: 'Mission initialized',
        }),
      };
    });

    const payload: MissionInitPayload = {
      mission_title: ' Test Mission Title ',
      mission_objective: ' Test Objective ',
      priority: 'high',
    };

    const res = await apiClient.initMission(payload);

    assert.ok(capturedUrl.includes('/api/agent/init'));
    assert.strictEqual(capturedMethod, 'POST');
    assert.strictEqual(capturedBody.mission_title, 'Test Mission Title');
    assert.strictEqual(capturedBody.mission_objective, 'Test Objective');
    assert.strictEqual(capturedBody.priority, 'high');
    assert.strictEqual(res.mission_id, 'test-mission-123');
    assert.strictEqual(res.status, 'INITIALIZED');
  });

  it('Initialization failure throws descriptive error without raw stack trace', async () => {
    mockFetch(async () => ({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'mission_title must be non-empty string' }),
    }));

    await assert.rejects(
      async () => {
        await apiClient.initMission({ mission_title: '', mission_objective: 'Obj' });
      },
      (err: Error) => {
        assert.strictEqual(err.message, 'mission_title must be non-empty string');
        return true;
      }
    );
  });

  it('Feed polling calls GET /api/agent/feed with mission_id', async () => {
    let capturedUrl = '';

    mockFetch(async (url) => {
      capturedUrl = url;
      return {
        ok: true,
        status: 200,
        json: async () => ({
          mission_id: 'test-mission-123',
          entries: [
            {
              id: 'e1',
              mission_id: 'test-mission-123',
              current_stage: 'Planning',
              timestamp: '2026-08-08T08:01:00Z',
              agent_responsible: 'PlannerAgent',
              progress_percentage: 20,
              summary_of_work: 'Planning completed',
              decision_made: 'Plan structured',
              confidence: 0.95,
              event_type: 'STAGE_PROGRESS',
            },
          ],
          total_count: 1,
        }),
      };
    });

    const res = await apiClient.getMissionFeed('test-mission-123', 50, 0);

    assert.ok(capturedUrl.includes('/api/agent/feed'));
    assert.ok(capturedUrl.includes('mission_id=test-mission-123'));
    assert.strictEqual(res.entries.length, 1);
    assert.strictEqual(res.entries[0].id, 'e1');
  });

  it('Duplicate feed prevention retains unique IDs', () => {
    const rawEntries = [
      { id: 'e1', current_stage: 'Planning', timestamp: '2026-08-08T08:01:00Z' },
      { id: 'e1', current_stage: 'Planning', timestamp: '2026-08-08T08:01:00Z' },
      { id: 'e2', current_stage: 'Research', timestamp: '2026-08-08T08:02:00Z' },
    ];

    const seen = new Set<string>();
    const unique = rawEntries.filter((e) => {
      if (seen.has(e.id)) return false;
      seen.add(e.id);
      return true;
    });

    assert.strictEqual(unique.length, 2);
    assert.deepStrictEqual(
      unique.map((u) => u.id),
      ['e1', 'e2']
    );
  });

  it('Health check calls /health and returns service status', async () => {
    mockFetch(async () => ({
      ok: true,
      status: 200,
      json: async () => ({ status: 'ok', service: 'Autonomous Intelligence Core' }),
    }));

    const res = await apiClient.checkHealth();
    assert.strictEqual(res.status, 'ok');
    assert.strictEqual(res.service, 'Autonomous Intelligence Core');
  });
});
