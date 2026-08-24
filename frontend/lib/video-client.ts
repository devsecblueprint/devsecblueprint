/**
 * Videos API client for the Builder Session Videos feature.
 *
 * Implements all video-related API calls using the existing
 * apiClient pattern for authenticated requests. Transforms snake_case
 * responses from the backend into camelCase for frontend consumption.
 */

import { apiClient } from './api';
import type { ApiResponse } from './api';
import type {
  AdminListVideosResponse,
  CatalogVideoItem,
  CatalogResponse,
  CreateVideoRequest,
  InstructorInfo,
  PlaybackTokenResponse,
  ProgressResponse,
  Video,
  VideoFilters,
  VideoStatus,
  ResourceLink,
  UpdateVideoRequest,
} from './video-types';

// ---------------------------------------------------------------------------
// Response transformers (snake_case -> camelCase)
// ---------------------------------------------------------------------------

function transformVideo(raw: Record<string, unknown>): Video {
  return {
    id: raw.id as string,
    title: raw.title as string,
    slug: raw.slug as string,
    description: (raw.description as string) || '',
    thumbnailUrl: (raw.thumbnail_url as string) || null,
    durationSeconds: (raw.duration_seconds as number) || 0,
    instructor: raw.instructor as string,
    instructors: ((raw.instructors as Array<Record<string, unknown>>) || []).map(
      (i) => ({
        name: (i.name as string) || '',
        linkedinUrl: (i.linkedin_url as string) || null,
      })
    ),
    recordedAt: raw.recorded_at as string,
    status: raw.status as VideoStatus,
    tags: (raw.tags as string[]) || [],
    resources: ((raw.resources as Array<Record<string, string>>) || []).map(
      (r) => ({ title: r.title, url: r.url } as ResourceLink)
    ),
    createdAt: raw.created_at as string,
    updatedAt: raw.updated_at as string,
    publishedAt: (raw.published_at as string) || null,
  };
}

function transformCatalogItem(
  raw: Record<string, unknown>
): CatalogVideoItem {
  return {
    id: raw.id as string,
    title: raw.title as string,
    slug: raw.slug as string,
    thumbnailUrl: (raw.thumbnail_url as string) || null,
    durationSeconds: (raw.duration_seconds as number) || 0,
    tags: (raw.tags as string[]) || [],
    publishedAt: raw.published_at as string,
    progressPercent: (raw.progress_percent as number) || 0,
    positionSeconds: (raw.position_seconds as number) || null,
    lastWatchedAt: (raw.last_watched_at as string) || null,
  };
}

function transformCatalog(raw: Record<string, unknown>): CatalogResponse {
  const continueWatching = (
    (raw.continue_watching as Array<Record<string, unknown>>) || []
  ).map(transformCatalogItem);
  const latest = (
    (raw.latest as Array<Record<string, unknown>>) || []
  ).map(transformCatalogItem);
  const allPublished = (
    (raw.all_published as Array<Record<string, unknown>>) || []
  ).map(transformCatalogItem);

  return {
    continueWatching,
    latest,
    allPublished,
    totalCount: (raw.total_count as number) || 0,
    page: (raw.page as number) || 1,
    pageSize: (raw.page_size as number) || 20,
  };
}

function transformProgress(
  raw: Record<string, unknown>
): ProgressResponse {
  return {
    positionSeconds: (raw.position_seconds as number) ?? null,
    durationSeconds: (raw.duration_seconds as number) ?? null,
    percentComplete: (raw.percent_complete as number) ?? null,
    completed: (raw.completed as boolean) ?? null,
    lastWatchedAt: (raw.last_watched_at as string) ?? null,
  };
}

function transformPlaybackToken(
  raw: Record<string, unknown>
): PlaybackTokenResponse {
  return {
    token: raw.token as string,
    expiresInSeconds: (raw.expires_in_seconds as number) || 0,
  };
}

// ---------------------------------------------------------------------------
// Member endpoints
// ---------------------------------------------------------------------------

/**
 * Fetch the videos catalog for the authenticated member.
 */
export async function fetchCatalog(
  filters?: VideoFilters
): Promise<ApiResponse<CatalogResponse>> {
  const params = new URLSearchParams();
  if (filters?.page) params.set('page', String(filters.page));
  if (filters?.pageSize) params.set('page_size', String(filters.pageSize));
  if (filters?.search) params.set('search', filters.search);
  if (filters?.tags?.length) params.set('tags', filters.tags.join(','));
  if (filters?.instructor) params.set('instructor', filters.instructor);

  const query = params.toString();
  const endpoint = `/api/videos${query ? `?${query}` : ''}`;
  const response = await apiClient.get<Record<string, unknown>>(endpoint);

  if (response.data) {
    return { data: transformCatalog(response.data), statusCode: response.statusCode };
  }
  return { error: response.error, statusCode: response.statusCode };
}

/**
 * Fetch a single video by ID or slug.
 */
export async function fetchVideo(
  idOrSlug: string
): Promise<ApiResponse<Video>> {
  const response = await apiClient.get<Record<string, unknown>>(
    `/api/videos/${idOrSlug}`
  );

  if (response.data) {
    return { data: transformVideo(response.data), statusCode: response.statusCode };
  }
  return { error: response.error, statusCode: response.statusCode };
}

/**
 * Request a signed playback token for a video.
 */
export async function requestPlaybackToken(
  videoId: string
): Promise<ApiResponse<PlaybackTokenResponse>> {
  const response = await apiClient.post<Record<string, unknown>>(
    `/api/videos/${videoId}/playback`,
    {}
  );

  if (response.data) {
    return { data: transformPlaybackToken(response.data), statusCode: response.statusCode };
  }
  return { error: response.error, statusCode: response.statusCode };
}

/**
 * Fetch the user's progress for a specific video.
 */
export async function fetchProgress(
  videoId: string
): Promise<ApiResponse<ProgressResponse>> {
  const response = await apiClient.get<Record<string, unknown>>(
    `/api/videos/${videoId}/progress`
  );

  if (response.data) {
    return { data: transformProgress(response.data), statusCode: response.statusCode };
  }
  return { error: response.error, statusCode: response.statusCode };
}

/**
 * Save playback progress for a video.
 */
export async function saveProgress(
  videoId: string,
  positionSeconds: number,
  durationSeconds: number
): Promise<ApiResponse<{ percentComplete: number; completed: boolean }>> {
  const response = await apiClient.put<Record<string, unknown>>(
    `/api/videos/${videoId}/progress`,
    {
      position_seconds: positionSeconds,
      duration_seconds: durationSeconds,
    }
  );

  if (response.data) {
    return {
      data: {
        percentComplete: (response.data.percent_complete as number) || 0,
        completed: (response.data.completed as boolean) || false,
      },
      statusCode: response.statusCode,
    };
  }
  return { error: response.error, statusCode: response.statusCode };
}

// ---------------------------------------------------------------------------
// Admin endpoints
// ---------------------------------------------------------------------------

/**
 * List all videos with optional status filter (admin).
 */
export async function adminListVideos(
  status?: VideoStatus,
  page: number = 1,
  pageSize: number = 20
): Promise<ApiResponse<AdminListVideosResponse>> {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  params.set('page', String(page));
  params.set('page_size', String(pageSize));

  const response = await apiClient.get<Record<string, unknown>>(
    `/admin/videos?${params.toString()}`
  );

  if (response.data) {
    const rawVideos = (
      (response.data.recordings as Array<Record<string, unknown>>) || []
    ).map(transformVideo);
    return {
      data: {
        recordings: rawVideos,
        totalCount: (response.data.total_count as number) || 0,
        page: (response.data.page as number) || 1,
        pageSize: (response.data.page_size as number) || 20,
      },
      statusCode: response.statusCode,
    };
  }
  return { error: response.error, statusCode: response.statusCode };
}

/**
 * Create a new video (admin).
 */
export async function adminCreateVideo(
  data: CreateVideoRequest
): Promise<ApiResponse<Video>> {
  const response = await apiClient.post<Record<string, unknown>>(
    '/admin/videos',
    {
      title: data.title,
      description: data.description || '',
      cloudflare_stream_id: data.cloudflareStreamId,
      instructor: data.instructor,
      recorded_at: data.recordedAt,
      tags: data.tags || [],
      resources: data.resources || [],
      thumbnail_url: data.thumbnailUrl || null,
    }
  );

  if (response.data) {
    return { data: transformVideo(response.data), statusCode: response.statusCode };
  }
  return { error: response.error, statusCode: response.statusCode };
}

/**
 * Update video metadata (admin).
 */
export async function adminUpdateVideo(
  videoId: string,
  data: UpdateVideoRequest
): Promise<ApiResponse<Video>> {
  const body: Record<string, unknown> = {};
  if (data.title !== undefined) body.title = data.title;
  if (data.description !== undefined) body.description = data.description;
  if (data.instructor !== undefined) body.instructor = data.instructor;
  if (data.instructors !== undefined) {
    body.instructors = data.instructors.map((i) => ({
      name: i.name,
      linkedin_url: i.linkedinUrl || null,
    }));
  }
  if (data.tags !== undefined) body.tags = data.tags;
  if (data.resources !== undefined) body.resources = data.resources;
  if (data.thumbnailUrl !== undefined) body.thumbnail_url = data.thumbnailUrl;

  const response = await apiClient.put<Record<string, unknown>>(
    `/admin/videos/${videoId}`,
    body
  );

  if (response.data) {
    return { data: transformVideo(response.data), statusCode: response.statusCode };
  }
  return { error: response.error, statusCode: response.statusCode };
}

/**
 * Transition video status (admin).
 */
export async function adminTransitionStatus(
  videoId: string,
  targetStatus: VideoStatus
): Promise<ApiResponse<Video>> {
  const response = await apiClient.post<Record<string, unknown>>(
    `/admin/videos/${videoId}/status`,
    { target_status: targetStatus }
  );

  if (response.data) {
    return { data: transformVideo(response.data), statusCode: response.statusCode };
  }
  return { error: response.error, statusCode: response.statusCode };
}

/**
 * Check Cloudflare Stream processing status (admin).
 */
export async function adminCheckStreamStatus(
  videoId: string
): Promise<ApiResponse<Video>> {
  const response = await apiClient.get<Record<string, unknown>>(
    `/admin/videos/${videoId}/stream-status`
  );

  if (response.data) {
    return { data: transformVideo(response.data), statusCode: response.statusCode };
  }
  return { error: response.error, statusCode: response.statusCode };
}

// ---------------------------------------------------------------------------
// Public endpoints (no authentication required)
// ---------------------------------------------------------------------------

/**
 * Public video item returned by the public preview endpoints.
 */
export interface PublicVideoItem {
  id: string;
  title: string;
  slug: string;
  description: string;
  thumbnailUrl: string | null;
  durationSeconds: number;
  tags: string[];
  instructor: string;
  instructors: Array<{ name: string; linkedinUrl: string | null }>;
  recordedAt: string;
  publishedAt: string | null;
}

/**
 * Response from the public videos listing endpoint.
 */
export interface PublicVideosResponse {
  videos: PublicVideoItem[];
  totalCount: number;
  page: number;
  pageSize: number;
}

function transformPublicVideo(raw: Record<string, unknown>): PublicVideoItem {
  return {
    id: raw.id as string,
    title: raw.title as string,
    slug: raw.slug as string,
    description: (raw.description as string) || '',
    thumbnailUrl: (raw.thumbnail_url as string) || null,
    durationSeconds: (raw.duration_seconds as number) || 0,
    tags: (raw.tags as string[]) || [],
    instructor: (raw.instructor as string) || '',
    instructors: ((raw.instructors as Array<Record<string, unknown>>) || []).map(
      (i) => ({
        name: (i.name as string) || '',
        linkedinUrl: (i.linkedin_url as string) || null,
      })
    ),
    recordedAt: raw.recorded_at as string,
    publishedAt: (raw.published_at as string) || null,
  };
}

/**
 * Fetch published videos for public preview (no auth required).
 */
export async function fetchPublicVideos(
  page: number = 1,
  pageSize: number = 20
): Promise<ApiResponse<PublicVideosResponse>> {
  const params = new URLSearchParams();
  params.set('page', String(page));
  params.set('page_size', String(pageSize));

  const response = await apiClient.get<Record<string, unknown>>(
    `/public/videos?${params.toString()}`
  );

  if (response.data) {
    const rawVideos = (
      (response.data.videos as Array<Record<string, unknown>>) || []
    ).map(transformPublicVideo);
    return {
      data: {
        videos: rawVideos,
        totalCount: (response.data.total_count as number) || 0,
        page: (response.data.page as number) || 1,
        pageSize: (response.data.page_size as number) || 20,
      },
      statusCode: response.statusCode,
    };
  }
  return { error: response.error, statusCode: response.statusCode };
}

/**
 * Fetch a single public video by slug (no auth required).
 */
export async function fetchPublicVideo(
  slug: string
): Promise<ApiResponse<PublicVideoItem>> {
  const response = await apiClient.get<Record<string, unknown>>(
    `/public/videos/${slug}`
  );

  if (response.data) {
    return { data: transformPublicVideo(response.data), statusCode: response.statusCode };
  }
  return { error: response.error, statusCode: response.statusCode };
}
