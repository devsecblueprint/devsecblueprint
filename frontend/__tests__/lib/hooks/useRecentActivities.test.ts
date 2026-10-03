/**
 * Unit tests for useRecentActivities — covers fetch states plus the
 * dedup/relative-time/formatting transforms via the hook output.
 */
import { renderHook, waitFor, act } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { triggerProgressUpdate } from '@/lib/events';
import { useRecentActivities } from '@/lib/hooks/useRecentActivities';

jest.mock('@/lib/api', () => ({ apiClient: { getRecentActivities: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function item(content_id: string, completed_at: string) {
  return { content_id, status: 'complete', completed_at };
}

beforeEach(() => jest.clearAllMocks());

it('transforms activities with titles and relative time', async () => {
  const now = new Date().toISOString();
  mockApi.getRecentActivities.mockResolvedValue({
    data: { recent: [item('some_topic/intro_lesson', now)] },
    statusCode: 200,
  });
  const { result } = renderHook(() => useRecentActivities());
  await waitFor(() => expect(result.current.isLoading).toBe(false));

  expect(result.current.activities).toHaveLength(1);
  const a = result.current.activities[0];
  expect(a.title).toBe('Intro Lesson');
  expect(a.relativeTime).toBe('Just now');
});

it('deduplicates by normalized content id keeping the most recent', async () => {
  const older = '2026-01-01T00:00:00.000Z';
  const newer = '2026-02-01T00:00:00.000Z';
  mockApi.getRecentActivities.mockResolvedValue({
    data: {
      recent: [
        item('path/My_Lesson', older),
        item('path/my-lesson', newer), // same after normalization
      ],
    },
    statusCode: 200,
  });
  const { result } = renderHook(() => useRecentActivities());
  await waitFor(() => expect(result.current.isLoading).toBe(false));
  expect(result.current.activities).toHaveLength(1);
  expect(result.current.activities[0].completedAt).toBe(newer);
});

it('formats older timestamps as day/hour/minute strings', async () => {
  const threeDaysAgo = new Date(Date.now() - 3 * 86400000).toISOString();
  mockApi.getRecentActivities.mockResolvedValue({
    data: { recent: [item('p/lesson_a', threeDaysAgo)] },
    statusCode: 200,
  });
  const { result } = renderHook(() => useRecentActivities());
  await waitFor(() => expect(result.current.isLoading).toBe(false));
  expect(result.current.activities[0].relativeTime).toBe('3 days ago');
});

it('sets error on failure', async () => {
  mockApi.getRecentActivities.mockResolvedValue({ error: 'boom', statusCode: 500 });
  const { result } = renderHook(() => useRecentActivities());
  await waitFor(() => expect(result.current.isLoading).toBe(false));
  expect(result.current.error).toBe('boom');
  expect(result.current.activities).toEqual([]);
});

it('refetches on progress update', async () => {
  mockApi.getRecentActivities.mockResolvedValue({ data: { recent: [] }, statusCode: 200 });
  renderHook(() => useRecentActivities());
  await waitFor(() => expect(mockApi.getRecentActivities).toHaveBeenCalledTimes(1));
  act(() => triggerProgressUpdate());
  await waitFor(() => expect(mockApi.getRecentActivities).toHaveBeenCalledTimes(2));
});
