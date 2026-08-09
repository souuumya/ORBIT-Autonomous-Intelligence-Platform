import { describe, it, afterEach } from 'node:test';
import assert from 'node:assert';
import { apiClient } from '../lib/api-client';

const originalFetch = global.fetch;

function mockFetch(handler: (url: string, init?: RequestInit) => Promise<{ ok: boolean; status: number; json: () => Promise<any> }>) {
  global.fetch = (async (url: string, init?: RequestInit) => {
    return handler(url, init);
  }) as unknown as typeof fetch;
}

describe('Phase 4 — Decision Replay Verification', () => {
  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('Fetches real decision replay timeline from GET /api/agent/replay', async () => {
    let capturedUrl = '';
    let capturedMethod = '';

    mockFetch(async (url, init) => {
      capturedUrl = url;
      capturedMethod = init?.method || 'GET';
      return {
        ok: true,
        status: 200,
        json: async () => ({
          mission_id: 'm-123',
          total_steps: 3,
          steps: [
            {
              id: 's1',
              mission_id: 'm-123',
              step_number: 1,
              timestamp: '2026-08-08T08:00:00Z',
              agent: 'System',
              action_type: 'MISSION_STARTED',
              reason: 'Started mission',
              confidence: 1.0,
              duration_ms: 0,
              output_summary: 'Objective set',
              metadata: {},
            },
            {
              id: 's2',
              mission_id: 'm-123',
              step_number: 2,
              timestamp: '2026-08-08T08:01:00Z',
              agent: 'DecisionAgent',
              action_type: 'DECISION',
              reason: 'Goal analysis confirmed high score for Strategy C',
              confidence: 0.94,
              duration_ms: 320,
              output_summary: 'Selected Strategy C',
              metadata: {
                selected_strategy: { title: 'Strategy C: Comprehensive Execution', score: 0.94 },
                rejected_strategies: [
                  { title: 'Strategy A: Fast Prototyping', reason: 'Lower depth of coverage' },
                ],
              },
            },
          ],
        }),
      };
    });

    const replayData = await apiClient.getMissionReplay('m-123');

    assert.ok(capturedUrl.includes('/api/agent/replay'));
    assert.ok(capturedUrl.includes('mission_id=m-123'));
    assert.strictEqual(capturedMethod, 'GET');
    assert.ok(replayData !== null);
    assert.strictEqual(replayData?.total_steps, 3);
    assert.strictEqual(replayData?.steps[1].agent, 'DecisionAgent');
    assert.strictEqual(replayData?.steps[1].action_type, 'DECISION');
    assert.strictEqual(replayData?.steps[1].confidence, 0.94);
  });

  it('Correctly extracts selected strategy and rejected alternatives from replay metadata', async () => {
    mockFetch(async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        mission_id: 'm-456',
        total_steps: 1,
        steps: [
          {
            id: 's1',
            mission_id: 'm-456',
            step_number: 1,
            timestamp: '2026-08-08T08:05:00Z',
            agent: 'DecisionAgent',
            action_type: 'DECISION',
            reason: 'Top weighted candidate score based on domain evidence.',
            confidence: 0.95,
            duration_ms: 450,
            output_summary: 'Selected Strategy B',
            metadata: {
              selected_strategy: { title: 'Strategy B: Hybrid Approach', score: 0.95 },
              rejected_strategies: [
                { title: 'Strategy A: Rapid Agile', reason: 'Higher execution risk' },
                { title: 'Strategy C: Minimal Baseline', reason: 'Insufficient coverage' },
              ],
            },
          },
        ],
      }),
    }));

    const replayData = await apiClient.getMissionReplay('m-456');
    const decStep = replayData?.steps[0];
    const meta = decStep?.metadata as any;

    assert.strictEqual(meta.selected_strategy.title, 'Strategy B: Hybrid Approach');
    assert.strictEqual(meta.rejected_strategies.length, 2);
    assert.strictEqual(meta.rejected_strategies[0].title, 'Strategy A: Rapid Agile');
    assert.strictEqual(meta.rejected_strategies[0].reason, 'Higher execution risk');
  });

  it('Handles invalid mission ID or unavailable replay gracefully without crashing', async () => {
    mockFetch(async () => ({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Mission not found' }),
    }));

    const res = await apiClient.getMissionReplay('invalid-id');
    assert.strictEqual(res, null);
  });

  it('Guarantees read-only behavior: Replay operations NEVER issue POST /api/agent/init or mutations', async () => {
    const issuedMethods: string[] = [];

    mockFetch(async (url, init) => {
      issuedMethods.push(init?.method || 'GET');
      return {
        ok: true,
        status: 200,
        json: async () => ({ mission_id: 'm-789', total_steps: 0, steps: [] }),
      };
    });

    await apiClient.getMissionReplay('m-789');
    await apiClient.getMissionReflection('m-789');

    assert.ok(issuedMethods.every((m) => m === 'GET'));
    assert.strictEqual(issuedMethods.includes('POST' as any), false);
  });
});

