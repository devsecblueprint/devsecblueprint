/**
 * Additional unit tests for lib/walkthrough-client (filtering + progress enrichment).
 */
import { apiClient } from '@/lib/api';
import { getWalkthroughsWithProgress, updateWalkthroughProgress } from '@/lib/walkthrough-client';
import { WALKTHROUGHS_DATA } from '@/lib/walkthroughs-data';

jest.mock('@/lib/api', () => ({
  apiClient: { getWalkthroughProgress: jest.fn(), updateWalkthroughProgress: jest.fn() },
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

beforeEach(() => {
  jest.clearAllMocks();
  mockApi.getWalkthroughProgress.mockResolvedValue({
    data: { progress: { status: 'not_started' } },
    statusCode: 200,
  });
});

const sample = WALKTHROUGHS_DATA[0];

it('returns all walkthroughs without progress when includeProgress is false', async () => {
  const result = await getWalkthroughsWithProgress(undefined, false);
  expect(result.length).toBe(WALKTHROUGHS_DATA.length);
  expect(result.every((w) => w.progress.status === 'not_started')).toBe(true);
  expect(mockApi.getWalkthroughProgress).not.toHaveBeenCalled();
});

it('enriches walkthroughs with backend progress', async () => {
  mockApi.getWalkthroughProgress.mockResolvedValue({
    data: { progress: { status: 'in_progress', started_at: '2026-01-01', completed_at: null } },
    statusCode: 200,
  });
  const result = await getWalkthroughsWithProgress();
  expect(result.length).toBe(WALKTHROUGHS_DATA.length);
  expect(result[0].progress.status).toBe('in_progress');
  expect(mockApi.getWalkthroughProgress).toHaveBeenCalled();
});

it('filters by difficulty', async () => {
  const result = await getWalkthroughsWithProgress({ difficulty: sample.difficulty }, false);
  expect(result.every((w) => w.difficulty === sample.difficulty)).toBe(true);
});

it('filters by search term', async () => {
  const term = sample.title.split(' ')[0];
  const result = await getWalkthroughsWithProgress({ search: term }, false);
  expect(result.length).toBeGreaterThan(0);
  expect(result.every((w) =>
    w.title.toLowerCase().includes(term.toLowerCase()) ||
    w.description.toLowerCase().includes(term.toLowerCase()) ||
    w.topics.some((t) => t.toLowerCase().includes(term.toLowerCase())),
  )).toBe(true);
});

it('filters by topics', async () => {
  const topic = sample.topics[0];
  const result = await getWalkthroughsWithProgress({ topics: [topic] }, false);
  expect(result.every((w) => w.topics.includes(topic))).toBe(true);
});

it('filters by progress status (requires enrichment)', async () => {
  mockApi.getWalkthroughProgress.mockResolvedValue({
    data: { progress: { status: 'completed', started_at: '2026-01-01', completed_at: '2026-02-01' } },
    statusCode: 200,
  });
  const result = await getWalkthroughsWithProgress({ status: 'completed' });
  expect(result.every((w) => w.progress.status === 'completed')).toBe(true);
});

it('defaults to not_started when the progress fetch throws', async () => {
  mockApi.getWalkthroughProgress.mockRejectedValue(new Error('offline'));
  const spy = jest.spyOn(console, 'warn').mockImplementation(() => {});
  const result = await getWalkthroughsWithProgress();
  expect(result[0].progress.status).toBe('not_started');
  spy.mockRestore();
});

describe('updateWalkthroughProgress', () => {
  it('returns success on a clean update', async () => {
    mockApi.updateWalkthroughProgress.mockResolvedValue({ data: { message: 'ok' }, statusCode: 200 });
    expect(await updateWalkthroughProgress('wt-1', 'completed')).toEqual({ success: true });
  });

  it('returns the error from the API', async () => {
    mockApi.updateWalkthroughProgress.mockResolvedValue({ error: 'denied', statusCode: 403 });
    expect(await updateWalkthroughProgress('wt-1', 'in_progress')).toEqual({ success: false, error: 'denied' });
  });

  it('returns a failure when the call throws', async () => {
    mockApi.updateWalkthroughProgress.mockRejectedValue(new Error('network'));
    const res = await updateWalkthroughProgress('wt-1', 'completed');
    expect(res.success).toBe(false);
    expect(res.error).toBe('network');
  });
});
