/**
 * Unit tests for useVideos and useVideo.
 */
import { renderHook, waitFor } from '@testing-library/react';
import * as videoClient from '@/lib/video-client';
import { useVideos, useVideo } from '@/lib/hooks/useVideos';

jest.mock('@/lib/video-client', () => ({
  fetchCatalog: jest.fn(),
  fetchVideo: jest.fn(),
}));
const mockVc = videoClient as jest.Mocked<typeof videoClient>;

beforeEach(() => jest.clearAllMocks());

describe('useVideos', () => {
  it('loads the catalog', async () => {
    const catalog = { continueWatching: [], latest: [], allPublished: [], totalCount: 0, page: 1, pageSize: 20 };
    mockVc.fetchCatalog.mockResolvedValue({ data: catalog, statusCode: 200 });
    const { result } = renderHook(() => useVideos());
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.catalog).toBe(catalog);
    expect(result.current.error).toBeNull();
  });

  it('sets an error when the catalog fails', async () => {
    mockVc.fetchCatalog.mockResolvedValue({ error: 'boom', statusCode: 500 });
    const { result } = renderHook(() => useVideos({ search: 'k8s' }));
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe('boom');
    expect(result.current.catalog).toBeNull();
  });
});

describe('useVideo', () => {
  it('loads a single video', async () => {
    mockVc.fetchVideo.mockResolvedValue({ data: { id: 'v1', slug: 's' } as never, statusCode: 200 });
    const { result } = renderHook(() => useVideo('s'));
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.video).toMatchObject({ id: 'v1' });
  });

  it('does not fetch when slug is empty', async () => {
    const { result } = renderHook(() => useVideo(''));
    // isLoading stays true because fetchData returns early without resolving state
    await waitFor(() => expect(mockVc.fetchVideo).not.toHaveBeenCalled());
    expect(result.current.video).toBeNull();
  });

  it('reports an error on failure', async () => {
    mockVc.fetchVideo.mockResolvedValue({ error: 'gone', statusCode: 404 });
    const { result } = renderHook(() => useVideo('missing'));
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe('gone');
  });
});
