/**
 * Unit tests for useBuilderJourney.
 */
import { renderHook, waitFor, act } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { useBuilderJourney } from '@/lib/hooks/useBuilderJourney';
import { FREE_JOURNEY_PHASES, FREE_JOURNEY_TOTAL_TASKS } from '@/lib/data/builder-journey';

jest.mock('@/lib/api', () => ({ apiClient: { get: jest.fn(), put: jest.fn(), delete: jest.fn() } }));
jest.mock('@/lib/utils/journey-analytics', () => ({ trackJourneyEvent: jest.fn() }));
jest.mock('next/navigation', () => ({ usePathname: () => '/dashboard' }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

const firstTaskId = FREE_JOURNEY_PHASES[0].tasks[0].id;

function journeyResponse(overrides: Record<string, unknown> = {}) {
  return {
    data: {
      tasks: [],
      current_phase: 1,
      completion_percentage: 0,
      is_complete: false,
      journey_started_at: null,
      tier: 'FREE',
      ...overrides,
    },
    statusCode: 200,
  };
}

beforeEach(() => jest.clearAllMocks());

it('loads journey state and recommends the first task', async () => {
  mockApi.get.mockResolvedValue(journeyResponse());
  const { result } = renderHook(() => useBuilderJourney());
  await waitFor(() => expect(result.current.isLoading).toBe(false));

  expect(result.current.tier).toBe('FREE');
  expect(result.current.completionPercentage).toBe(0);
  expect(result.current.recommendedAction?.id).toBe(firstTaskId);
});

it('marks notEligible on a 403', async () => {
  mockApi.get.mockResolvedValue({ error: 'forbidden', statusCode: 403 });
  const { result } = renderHook(() => useBuilderJourney());
  await waitFor(() => expect(result.current.isLoading).toBe(false));
  expect(result.current.notEligible).toBe(true);
});

it('computes completion percentage from completed tasks', async () => {
  mockApi.get.mockResolvedValue(
    journeyResponse({
      tasks: [{ task_id: firstTaskId, phase: 1, status: 'completed', completed_at: '2026-01-01', auto_completed: false }],
    }),
  );
  const { result } = renderHook(() => useBuilderJourney());
  await waitFor(() => expect(result.current.isLoading).toBe(false));

  const expected = Math.round((1 / FREE_JOURNEY_TOTAL_TASKS) * 100);
  expect(result.current.completionPercentage).toBe(expected);
  expect(result.current.recentCompletions[0]?.taskId).toBe(firstTaskId);
});

it('sets error when the API returns an error', async () => {
  mockApi.get.mockResolvedValue({ error: 'boom', statusCode: 500 });
  const { result } = renderHook(() => useBuilderJourney());
  await waitFor(() => expect(result.current.isLoading).toBe(false));
  expect(result.current.error).toBe('boom');
});

it('completeTask optimistically updates and calls the API', async () => {
  mockApi.get.mockResolvedValue(journeyResponse());
  mockApi.put.mockResolvedValue({
    data: { task_id: firstTaskId, status: 'completed', completed_at: '2026-01-01', phase_completed: false, journey_completed: false },
    statusCode: 200,
  });
  const { result } = renderHook(() => useBuilderJourney());
  await waitFor(() => expect(result.current.isLoading).toBe(false));

  await act(async () => {
    await result.current.completeTask(firstTaskId);
  });
  expect(mockApi.put).toHaveBeenCalledWith('/progress/journey', { task_id: firstTaskId });
  expect(result.current.taskStatuses[firstTaskId].status).toBe('completed');
});

it('reverts the optimistic update when completeTask fails', async () => {
  mockApi.get.mockResolvedValue(journeyResponse());
  mockApi.put.mockResolvedValue({ error: 'denied', statusCode: 403 });
  const { result } = renderHook(() => useBuilderJourney());
  await waitFor(() => expect(result.current.isLoading).toBe(false));

  await act(async () => {
    await result.current.completeTask(firstTaskId);
  });
  expect(result.current.taskStatuses[firstTaskId]).toBeUndefined();
  expect(result.current.error).toBe('denied');
});

it('uncompleteTask removes the task and calls DELETE', async () => {
  mockApi.get.mockResolvedValue(
    journeyResponse({
      tasks: [{ task_id: firstTaskId, phase: 1, status: 'completed', completed_at: '2026-01-01', auto_completed: false }],
    }),
  );
  mockApi.delete.mockResolvedValue({ data: { message: 'ok' }, statusCode: 200 });
  const { result } = renderHook(() => useBuilderJourney());
  await waitFor(() => expect(result.current.taskStatuses[firstTaskId]?.status).toBe('completed'));

  await act(async () => {
    await result.current.uncompleteTask(firstTaskId);
  });
  expect(mockApi.delete).toHaveBeenCalledWith(`/progress/journey/${firstTaskId}`);
  expect(result.current.taskStatuses[firstTaskId]).toBeUndefined();
});
