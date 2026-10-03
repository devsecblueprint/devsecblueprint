/**
 * Unit tests for lib/hooks/useUserStats.
 */
import { renderHook, waitFor, act } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { triggerProgressUpdate } from '@/lib/events';
import { useUserStats } from '@/lib/hooks/useUserStats';

jest.mock('@/lib/api', () => ({ apiClient: { getStats: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

const STATS = {
  current_streak: 3,
  longest_streak: 7,
  overall_completion: 42,
  completed_count: 10,
  quizzes_passed: 4,
  walkthroughs_completed: 2,
};

beforeEach(() => jest.clearAllMocks());

it('loads stats from the backend', async () => {
  mockApi.getStats.mockResolvedValue({ data: STATS, statusCode: 200 });
  const { result } = renderHook(() => useUserStats());

  expect(result.current.isLoading).toBe(true);
  await waitFor(() => expect(result.current.isLoading).toBe(false));

  expect(result.current.currentStreak).toBe(3);
  expect(result.current.longestStreak).toBe(7);
  expect(result.current.overallCompletion).toBe(42);
  expect(result.current.error).toBeNull();
});

it('surfaces a backend error and zeroes stats', async () => {
  mockApi.getStats.mockResolvedValue({ error: 'failed', statusCode: 500 });
  const { result } = renderHook(() => useUserStats());
  await waitFor(() => expect(result.current.isLoading).toBe(false));
  expect(result.current.error).toBe('failed');
  expect(result.current.completedCount).toBe(0);
});

it('handles a thrown exception', async () => {
  mockApi.getStats.mockRejectedValue(new Error('network down'));
  const { result } = renderHook(() => useUserStats());
  await waitFor(() => expect(result.current.isLoading).toBe(false));
  expect(result.current.error).toBe('network down');
});

it('refetches when a progress update event fires', async () => {
  mockApi.getStats.mockResolvedValue({ data: STATS, statusCode: 200 });
  const { result } = renderHook(() => useUserStats());
  await waitFor(() => expect(result.current.isLoading).toBe(false));
  expect(mockApi.getStats).toHaveBeenCalledTimes(1);

  act(() => triggerProgressUpdate());
  await waitFor(() => expect(mockApi.getStats).toHaveBeenCalledTimes(2));
});

it('clearError resets the error', async () => {
  mockApi.getStats.mockResolvedValue({ error: 'failed', statusCode: 500 });
  const { result } = renderHook(() => useUserStats());
  await waitFor(() => expect(result.current.error).toBe('failed'));
  act(() => result.current.clearError());
  expect(result.current.error).toBeNull();
});
