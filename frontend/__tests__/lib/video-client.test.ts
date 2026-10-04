/**
 * Unit tests for lib/video-client.ts.
 * apiClient is mocked; tests assert snake_case -> camelCase transforms,
 * correct endpoints/bodies, and error pass-through.
 */
import { apiClient } from '@/lib/api';
import * as vc from '@/lib/video-client';

jest.mock('@/lib/api', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
  },
}));

const mockApi = apiClient as jest.Mocked<typeof apiClient>;

beforeEach(() => jest.clearAllMocks());

describe('fetchCatalog', () => {
  it('transforms catalog sections and builds a filter query', async () => {
    mockApi.get.mockResolvedValueOnce({
      data: {
        continue_watching: [{ id: 'v1', title: 'A', slug: 'a', progress_percent: 50 }],
        latest: [{ id: 'v2', title: 'B', slug: 'b' }],
        all_published: [],
        total_count: 2,
        page: 1,
        page_size: 20,
      },
      statusCode: 200,
    });

    const res = await vc.fetchCatalog({ page: 1, pageSize: 20, search: 'k8s', tags: ['sec', 'aws'], instructor: 'ada' });
    expect(res.data?.continueWatching[0]).toMatchObject({ id: 'v1', progressPercent: 50 });
    expect(res.data?.latest[0].id).toBe('v2');
    expect(res.data?.totalCount).toBe(2);

    const endpoint = mockApi.get.mock.calls[0][0];
    expect(endpoint).toContain('search=k8s');
    expect(endpoint).toContain('tags=sec%2Caws');
    expect(endpoint).toContain('instructor=ada');
  });

  it('uses the bare endpoint when no filters are passed', async () => {
    mockApi.get.mockResolvedValueOnce({ data: {}, statusCode: 200 });
    await vc.fetchCatalog();
    expect(mockApi.get.mock.calls[0][0]).toBe('/api/videos');
  });

  it('passes through errors', async () => {
    mockApi.get.mockResolvedValueOnce({ error: 'boom', statusCode: 500 });
    const res = await vc.fetchCatalog();
    expect(res.error).toBe('boom');
    expect(res.data).toBeUndefined();
  });
});

describe('fetchVideo', () => {
  it('transforms a full video including instructors and resources', async () => {
    mockApi.get.mockResolvedValueOnce({
      data: {
        id: 'v1',
        title: 'Intro',
        slug: 'intro',
        duration_seconds: 120,
        instructor: 'Ada',
        instructors: [{ name: 'Ada', linkedin_url: 'https://linkedin.com/in/ada' }],
        resources: [{ title: 'Slides', url: 'https://x/y' }],
        status: 'published',
      },
      statusCode: 200,
    });
    const res = await vc.fetchVideo('intro');
    expect(res.data).toMatchObject({
      id: 'v1',
      durationSeconds: 120,
      instructors: [{ name: 'Ada', linkedinUrl: 'https://linkedin.com/in/ada' }],
      resources: [{ title: 'Slides', url: 'https://x/y' }],
    });
  });

  it('defaults missing optional fields', async () => {
    mockApi.get.mockResolvedValueOnce({ data: { id: 'v1', title: 't', slug: 's' }, statusCode: 200 });
    const res = await vc.fetchVideo('s');
    expect(res.data?.description).toBe('');
    expect(res.data?.durationSeconds).toBe(0);
    expect(res.data?.instructors).toEqual([]);
    expect(res.data?.thumbnailUrl).toBeNull();
  });
});

describe('requestPlaybackToken', () => {
  it('posts to the playback endpoint and transforms the token', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { token: 'tok', expires_in_seconds: 300 }, statusCode: 200 });
    const res = await vc.requestPlaybackToken('v1');
    expect(mockApi.post).toHaveBeenCalledWith('/api/videos/v1/playback', {});
    expect(res.data).toEqual({ token: 'tok', expiresInSeconds: 300 });
  });
});

describe('fetchProgress & saveProgress', () => {
  it('transforms progress nullables', async () => {
    mockApi.get.mockResolvedValueOnce({
      data: { position_seconds: 10, duration_seconds: 100, percent_complete: 10, completed: false, last_watched_at: 'now' },
      statusCode: 200,
    });
    const res = await vc.fetchProgress('v1');
    expect(res.data).toMatchObject({ positionSeconds: 10, percentComplete: 10, completed: false });
  });

  it('saves progress with snake_case body and returns computed fields', async () => {
    mockApi.put.mockResolvedValueOnce({ data: { percent_complete: 42, completed: false }, statusCode: 200 });
    const res = await vc.saveProgress('v1', 42, 100);
    expect(mockApi.put).toHaveBeenCalledWith('/api/videos/v1/progress', {
      position_seconds: 42,
      duration_seconds: 100,
    });
    expect(res.data).toEqual({ percentComplete: 42, completed: false });
  });

  it('passes through saveProgress errors', async () => {
    mockApi.put.mockResolvedValueOnce({ error: 'nope', statusCode: 400 });
    const res = await vc.saveProgress('v1', 1, 2);
    expect(res.error).toBe('nope');
  });
});

describe('admin endpoints', () => {
  it('adminListVideos builds a status/page query and maps recordings', async () => {
    mockApi.get.mockResolvedValueOnce({
      data: { recordings: [{ id: 'v1', title: 't', slug: 's' }], total_count: 1, page: 1, page_size: 20 },
      statusCode: 200,
    });
    const res = await vc.adminListVideos('published', 1, 20);
    expect(mockApi.get.mock.calls[0][0]).toContain('status=published');
    expect(res.data?.recordings).toHaveLength(1);
    expect(res.data?.totalCount).toBe(1);
  });

  it('adminCreateVideo maps camelCase request to snake_case body', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { id: 'v1', title: 'New', slug: 'new' }, statusCode: 201 });
    await vc.adminCreateVideo({
      title: 'New',
      cloudflareStreamId: 'cf1',
      instructor: 'Ada',
      recordedAt: '2026-01-01',
    } as never);
    const body = mockApi.post.mock.calls[0][1] as Record<string, unknown>;
    expect(body.cloudflare_stream_id).toBe('cf1');
    expect(body.recorded_at).toBe('2026-01-01');
  });

  it('adminUpdateVideo only includes provided fields', async () => {
    mockApi.put.mockResolvedValueOnce({ data: { id: 'v1', title: 'U', slug: 's' }, statusCode: 200 });
    await vc.adminUpdateVideo('v1', { title: 'U', instructors: [{ name: 'Ada', linkedinUrl: null }] } as never);
    const body = mockApi.put.mock.calls[0][1] as Record<string, unknown>;
    expect(body.title).toBe('U');
    expect(body).not.toHaveProperty('description');
    expect(body.instructors).toEqual([{ name: 'Ada', linkedin_url: null }]);
  });

  it('adminTransitionStatus posts the target status', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { id: 'v1', title: 't', slug: 's' }, statusCode: 200 });
    await vc.adminTransitionStatus('v1', 'published' as never);
    expect(mockApi.post).toHaveBeenCalledWith('/admin/videos/v1/status', { target_status: 'published' });
  });

  it('adminCheckStreamStatus hits the stream-status endpoint', async () => {
    mockApi.get.mockResolvedValueOnce({ data: { id: 'v1', title: 't', slug: 's' }, statusCode: 200 });
    await vc.adminCheckStreamStatus('v1');
    expect(mockApi.get).toHaveBeenCalledWith('/admin/videos/v1/stream-status');
  });
});

describe('public endpoints', () => {
  it('fetchPublicVideos maps the videos array', async () => {
    mockApi.get.mockResolvedValueOnce({
      data: { videos: [{ id: 'v1', title: 't', slug: 's' }], total_count: 1, page: 1, page_size: 20 },
      statusCode: 200,
    });
    const res = await vc.fetchPublicVideos();
    expect(res.data?.videos[0].id).toBe('v1');
    expect(mockApi.get.mock.calls[0][0]).toContain('/public/videos?');
  });

  it('fetchPublicVideo transforms a single public video', async () => {
    mockApi.get.mockResolvedValueOnce({ data: { id: 'v1', title: 't', slug: 's' }, statusCode: 200 });
    const res = await vc.fetchPublicVideo('s');
    expect(res.data?.slug).toBe('s');
  });

  it('passes through public fetch errors', async () => {
    mockApi.get.mockResolvedValueOnce({ error: 'gone', statusCode: 404 });
    const res = await vc.fetchPublicVideo('missing');
    expect(res.error).toBe('gone');
  });
});
