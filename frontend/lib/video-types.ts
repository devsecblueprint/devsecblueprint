/**
 * TypeScript types for the Builder Session Videos feature.
 *
 * Matches backend Pydantic models with camelCase naming convention.
 */

/**
 * Video lifecycle status values.
 */
export type VideoStatus =
  | 'DRAFT'
  | 'PROCESSING'
  | 'READY'
  | 'PUBLISHED'
  | 'ARCHIVED';

/**
 * A linked resource attached to a video (e.g., slide deck, repo).
 */
export interface ResourceLink {
  title: string;
  url: string;
}

/**
 * An instructor/author with optional LinkedIn profile URL.
 */
export interface InstructorInfo {
  name: string;
  linkedinUrl: string | null;
}

/**
 * Full video metadata (used for detail pages and admin views).
 */
export interface Video {
  id: string;
  title: string;
  slug: string;
  description: string;
  thumbnailUrl: string | null;
  durationSeconds: number;
  instructor: string;
  instructors: InstructorInfo[];
  recordedAt: string;
  status: VideoStatus;
  tags: string[];
  resources: ResourceLink[];
  createdAt: string;
  updatedAt: string;
  publishedAt: string | null;
}

/**
 * A single video entry in the catalog response.
 */
export interface CatalogVideoItem {
  id: string;
  title: string;
  slug: string;
  thumbnailUrl: string | null;
  durationSeconds: number;
  tags: string[];
  publishedAt: string;
  progressPercent: number;
  positionSeconds: number | null;
  lastWatchedAt: string | null;
}

/**
 * Response for the member videos catalog endpoint.
 */
export interface CatalogResponse {
  continueWatching: CatalogVideoItem[];
  latest: CatalogVideoItem[];
  allPublished: CatalogVideoItem[];
  totalCount: number;
  page: number;
  pageSize: number;
}

/**
 * Response containing a signed Cloudflare Stream playback token.
 */
export interface PlaybackTokenResponse {
  token: string;
  expiresInSeconds: number;
}

/**
 * Response for retrieving playback progress.
 */
export interface ProgressResponse {
  positionSeconds: number | null;
  durationSeconds: number | null;
  percentComplete: number | null;
  completed: boolean | null;
  lastWatchedAt: string | null;
}

/**
 * Filters for querying the videos catalog.
 */
export interface VideoFilters {
  search?: string;
  tags?: string[];
  instructor?: string;
  page?: number;
  pageSize?: number;
}

/**
 * Request body for creating a new video (admin).
 */
export interface CreateVideoRequest {
  title: string;
  description?: string;
  cloudflareStreamId: string;
  instructor: string;
  recordedAt: string;
  tags?: string[];
  resources?: ResourceLink[];
  thumbnailUrl?: string;
}

/**
 * Request body for updating video metadata (admin, partial).
 */
export interface UpdateVideoRequest {
  title?: string;
  description?: string;
  instructor?: string;
  instructors?: Array<{ name: string; linkedinUrl?: string }>;
  tags?: string[];
  resources?: ResourceLink[];
  thumbnailUrl?: string;
}

/**
 * Admin list videos response.
 */
export interface AdminListVideosResponse {
  recordings: Video[];
  totalCount: number;
  page: number;
  pageSize: number;
}
