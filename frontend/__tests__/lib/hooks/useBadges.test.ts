/**
 * Unit tests for lib/hooks/useBadges.
 */
import { renderHook, waitFor, act } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { useBadges } from '@/lib/hooks/useBadges';

jest.mock('@/lib/api', () => ({ apiClient: { getBadges: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function badge(id: string, earned: boolean) {
  return { id, title: id, description: 'd', icon: '🎯', earned, earned_date: earned ? 'now' : undefined };
}

beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
});

it('transforms and returns fetched badges', async () => {
  mockApi.getBadges.mockResolvedValue({
    data: { badges: [badge('b1', true), badge('b2', false)] },
    statusCode: 200,
  });
  const { result } = renderHook(() => useBadges());
  await waitFor(() => expect(result.current.isLoading).toBe(false));

  expect(result.current.badges).toHaveLength(2);
  expect(result.current.badges[0]).toMatchObject({ id: 'b1', earned: true, earnedDate: 'now' });
  expect(result.current.error).toBeNull();
});

it('falls back to default locked badges on error', async () => {
  mockApi.getBadges.mockResolvedValue({ error: 'nope', statusCode: 500 });
  const { result } = renderHook(() => useBadges());
  await waitFor(() => expect(result.current.isLoading).toBe(false));
  expect(result.current.error).toBe('nope');
  expect(result.current.badges.every((b) => !b.earned)).toBe(true);
});

it('detects newly earned badges against localStorage on first load', async () => {
  localStorage.setItem('earnedBadgeIds', JSON.stringify(['b1']));
  mockApi.getBadges.mockResolvedValue({
    data: { badges: [badge('b1', true), badge('b2', true)] },
    statusCode: 200,
  });
  const { result } = renderHook(() => useBadges());
  await waitFor(() => expect(result.current.isLoading).toBe(false));

  // b2 is newly earned (b1 was already stored)
  expect(result.current.newlyEarnedBadges.map((b) => b.id)).toEqual(['b2']);
  // store is updated to include both
  expect(JSON.parse(localStorage.getItem('earnedBadgeIds')!)).toEqual(['b1', 'b2']);
});

it('clearNewBadge dequeues the first newly earned badge', async () => {
  mockApi.getBadges.mockResolvedValue({
    data: { badges: [badge('b1', true), badge('b2', true)] },
    statusCode: 200,
  });
  const { result } = renderHook(() => useBadges());
  await waitFor(() => expect(result.current.newlyEarnedBadges.length).toBe(2));

  act(() => result.current.clearNewBadge());
  expect(result.current.newlyEarnedBadges.map((b) => b.id)).toEqual(['b2']);
});

it('refetches on a badge:check event', async () => {
  mockApi.getBadges.mockResolvedValue({ data: { badges: [badge('b1', false)] }, statusCode: 200 });
  renderHook(() => useBadges());
  await waitFor(() => expect(mockApi.getBadges).toHaveBeenCalledTimes(1));

  act(() => window.dispatchEvent(new CustomEvent('badge:check')));
  await waitFor(() => expect(mockApi.getBadges).toHaveBeenCalledTimes(2));
});
