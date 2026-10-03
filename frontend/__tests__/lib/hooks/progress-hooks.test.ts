/**
 * Unit tests for useProgress, useAllProgress, and useLastActiveLesson.
 */
import { renderHook, waitFor, act } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { useProgress } from '@/lib/hooks/useProgress';
import { useAllProgress } from '@/lib/hooks/useAllProgress';
import { useLastActiveLesson } from '@/lib/hooks/useLastActiveLesson';

jest.mock('@/lib/api', () => ({
  apiClient: {
    saveProgress: jest.fn(),
    getProgress: jest.fn(),
    getLastActiveLesson: jest.fn(),
  },
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

beforeEach(() => jest.clearAllMocks());

describe('useProgress', () => {
  it('rejects an invalid content id without calling the API', async () => {
    const { result } = renderHook(() => useProgress());
    let ok = true;
    await act(async () => {
      ok = await result.current.saveProgress('');
    });
    expect(ok).toBe(false);
    expect(result.current.error).toBe('Invalid content ID');
    expect(mockApi.saveProgress).not.toHaveBeenCalled();
  });

  it('saves progress successfully', async () => {
    mockApi.saveProgress.mockResolvedValue({ data: { message: 'ok' }, statusCode: 200 });
    const { result } = renderHook(() => useProgress());
    let ok = false;
    await act(async () => {
      ok = await result.current.saveProgress('page-1');
    });
    expect(ok).toBe(true);
    expect(result.current.lastSaved).toBe('page-1');
    expect(result.current.error).toBeNull();
  });

  it('reports a backend error', async () => {
    mockApi.saveProgress.mockResolvedValue({ error: 'denied', statusCode: 403 });
    const { result } = renderHook(() => useProgress());
    let ok = true;
    await act(async () => {
      ok = await result.current.saveProgress('page-1');
    });
    expect(ok).toBe(false);
    expect(result.current.error).toBe('denied');
  });

  it('handles a thrown exception', async () => {
    mockApi.saveProgress.mockRejectedValue(new Error('offline'));
    const { result } = renderHook(() => useProgress());
    await act(async () => {
      await result.current.saveProgress('page-1');
    });
    expect(result.current.error).toBe('offline');
  });
});

describe('useAllProgress', () => {
  it('maps progress items to a completion map', async () => {
    mockApi.getProgress.mockResolvedValue({
      data: {
        progress: [
          { content_id: 'a', status: 'complete', completed_at: 'now' },
          { content_id: 'b', status: 'in_progress', completed_at: '' },
        ],
      },
      statusCode: 200,
    });
    const { result } = renderHook(() => useAllProgress());
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.progress).toEqual({ a: true, b: false });
  });

  it('updateProgress mutates the local map', async () => {
    mockApi.getProgress.mockResolvedValue({ data: { progress: [] }, statusCode: 200 });
    const { result } = renderHook(() => useAllProgress());
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    act(() => result.current.updateProgress('c', true));
    expect(result.current.progress.c).toBe(true);
  });

  it('sets error on failure', async () => {
    mockApi.getProgress.mockResolvedValue({ error: 'boom', statusCode: 500 });
    const { result } = renderHook(() => useAllProgress());
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe('boom');
  });
});

describe('useLastActiveLesson', () => {
  it('returns the resume point when present', async () => {
    mockApi.getLastActiveLesson.mockResolvedValue({
      data: { page_id: 'p1', page_slug: 'intro' },
      statusCode: 200,
    });
    const { result } = renderHook(() => useLastActiveLesson());
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.pageId).toBe('p1');
    expect(result.current.pageSlug).toBe('intro');
  });

  it('returns nulls when the API throws', async () => {
    mockApi.getLastActiveLesson.mockRejectedValue(new Error('x'));
    const { result } = renderHook(() => useLastActiveLesson());
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.pageId).toBeNull();
  });
});
