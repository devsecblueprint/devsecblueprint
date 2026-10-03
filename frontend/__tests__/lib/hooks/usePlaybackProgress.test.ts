/**
 * Unit tests for usePlaybackProgress and usePlaybackToken.
 */
import { renderHook, waitFor, act } from '@testing-library/react';
import * as videoClient from '@/lib/video-client';
import { usePlaybackProgress, usePlaybackToken } from '@/lib/hooks/usePlaybackProgress';

jest.mock('@/lib/video-client', () => ({
  fetchProgress: jest.fn(),
  saveProgress: jest.fn(),
  requestPlaybackToken: jest.fn(),
}));
const mockVc = videoClient as jest.Mocked<typeof videoClient>;

beforeEach(() => jest.clearAllMocks());

describe('usePlaybackProgress', () => {
  it('loads initial progress', async () => {
    mockVc.fetchProgress.mockResolvedValue({
      data: { positionSeconds: 30, durationSeconds: 100, percentComplete: 30, completed: false, lastWatchedAt: null },
      statusCode: 200,
    });
    const { result } = renderHook(() => usePlaybackProgress('rec1'));
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.progress?.positionSeconds).toBe(30);
  });

  it('sets error when initial fetch fails', async () => {
    mockVc.fetchProgress.mockResolvedValue({ error: 'nope', statusCode: 500 });
    const { result } = renderHook(() => usePlaybackProgress('rec1'));
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe('nope');
  });

  it('saves immediately on a significant seek', async () => {
    mockVc.fetchProgress.mockResolvedValue({
      data: { positionSeconds: 0, durationSeconds: 100, percentComplete: 0, completed: false, lastWatchedAt: null },
      statusCode: 200,
    });
    mockVc.saveProgress.mockResolvedValue({ data: { percentComplete: 60, completed: false }, statusCode: 200 });

    const { result } = renderHook(() => usePlaybackProgress('rec1'));
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // Seek far from last saved position (0 -> 60)
    await act(async () => {
      result.current.saveCurrentProgress(60, 100);
    });
    await waitFor(() => expect(mockVc.saveProgress).toHaveBeenCalledWith('rec1', 60, 100));
  });

  it('does not save when duration is zero', async () => {
    mockVc.fetchProgress.mockResolvedValue({
      data: { positionSeconds: 0, durationSeconds: 100, percentComplete: 0, completed: false, lastWatchedAt: null },
      statusCode: 200,
    });
    const { result } = renderHook(() => usePlaybackProgress('rec1'));
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    await act(async () => {
      result.current.saveCurrentProgress(60, 0);
    });
    expect(mockVc.saveProgress).not.toHaveBeenCalled();
  });
});

describe('usePlaybackToken', () => {
  it('fetches a token', async () => {
    mockVc.requestPlaybackToken.mockResolvedValue({ data: { token: 'tok', expiresInSeconds: 300 }, statusCode: 200 });
    const { result } = renderHook(() => usePlaybackToken('rec1'));
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.token).toBe('tok');
    expect(result.current.expiresInSeconds).toBe(300);
  });

  it('sets error when token request fails', async () => {
    mockVc.requestPlaybackToken.mockResolvedValue({ error: 'denied', statusCode: 403 });
    const { result } = renderHook(() => usePlaybackToken('rec1'));
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe('denied');
  });

  it('refresh re-requests the token', async () => {
    mockVc.requestPlaybackToken.mockResolvedValue({ data: { token: 'tok', expiresInSeconds: 300 }, statusCode: 200 });
    const { result } = renderHook(() => usePlaybackToken('rec1'));
    await waitFor(() => expect(mockVc.requestPlaybackToken).toHaveBeenCalledTimes(1));
    await act(async () => {
      await result.current.refresh();
    });
    expect(mockVc.requestPlaybackToken).toHaveBeenCalledTimes(2);
  });
});
