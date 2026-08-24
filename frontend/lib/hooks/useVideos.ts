/**
 * Videos Hooks
 *
 * Provides data fetching hooks for the videos catalog and
 * individual video detail pages.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { fetchCatalog, fetchVideo } from '@/lib/video-client';
import type {
  CatalogResponse,
  Video,
  VideoFilters,
} from '@/lib/video-types';

/**
 * Hook return type for useVideos
 */
interface UseVideosReturn {
  catalog: CatalogResponse | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * Hook return type for useVideo
 */
interface UseVideoReturn {
  video: Video | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * Hook to fetch the videos catalog with optional filters.
 *
 * @param filters - Optional filters for search, tags, pagination.
 * @returns Catalog data, loading state, and error.
 */
export function useVideos(filters?: VideoFilters): UseVideosReturn {
  const [catalog, setCatalog] = useState<CatalogResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    const { data, error: apiError } = await fetchCatalog(filters);

    if (data) {
      setCatalog(data);
    } else {
      setError(apiError || 'Failed to load videos');
    }

    setIsLoading(false);
  }, [filters?.page, filters?.pageSize, filters?.search, filters?.tags?.join(','), filters?.instructor]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { catalog, isLoading, error, refetch: fetchData };
}

/**
 * Hook to fetch a single video by slug.
 *
 * @param slug - The video slug or ID.
 * @returns Video data, loading state, and error.
 */
export function useVideo(slug: string): UseVideoReturn {
  const [video, setVideo] = useState<Video | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!slug) return;

    setIsLoading(true);
    setError(null);

    const { data, error: apiError } = await fetchVideo(slug);

    if (data) {
      setVideo(data);
    } else {
      setError(apiError || 'Failed to load video');
    }

    setIsLoading(false);
  }, [slug]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { video, isLoading, error, refetch: fetchData };
}
