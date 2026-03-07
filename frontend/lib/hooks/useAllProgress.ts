/**
 * All Progress Hook
 * 
 * Fetches all user progress from the backend.
 * Note: Users must be authenticated to access pages that use this hook.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient, ProgressItem } from '@/lib/api';

/**
 * All progress state interface
 */
interface AllProgressState {
  progress: Record<string, boolean>;
  isLoading: boolean;
  error: string | null;
}

/**
 * All progress hook return type
 */
interface UseAllProgressReturn extends AllProgressState {
  refetch: () => Promise<void>;
  updateProgress: (contentId: string, completed: boolean) => void;
  clearError: () => void;
}

/**
 * Transform backend progress items to a map
 */
function transformProgressItems(items: ProgressItem[]): Record<string, boolean> {
  const progressMap: Record<string, boolean> = {};
  items.forEach(item => {
    progressMap[item.content_id] = item.status === 'complete';
  });
  return progressMap;
}

/**
 * useAllProgress Hook
 * 
 * Fetches all user progress from backend.
 * 
 * @returns All progress state and methods
 */
export function useAllProgress(): UseAllProgressReturn {
  const [state, setState] = useState<AllProgressState>({
    progress: {},
    isLoading: true,
    error: null,
  });

  /**
   * Fetch all progress from backend
   */
  const fetchProgress = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const { data, error } = await apiClient.getProgress();

      if (data) {
        const progressMap = transformProgressItems(data.progress);
        setState({
          progress: progressMap,
          isLoading: false,
          error: null,
        });
      } else {
        setState({
          progress: {},
          isLoading: false,
          error: error || 'Failed to fetch progress',
        });
      }
    } catch (error) {
      setState({
        progress: {},
        isLoading: false,
        error: error instanceof Error ? error.message : 'Network error',
      });
    }
  }, []);

  /**
   * Fetch progress on mount and when authentication changes
   */
  useEffect(() => {
    fetchProgress();
  }, [fetchProgress]);

  /**
   * Update progress locally without refetching
   */
  const updateProgress = useCallback((contentId: string, completed: boolean) => {
    setState(prev => ({
      ...prev,
      progress: {
        ...prev.progress,
        [contentId]: completed
      }
    }));
  }, []);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    ...state,
    refetch: fetchProgress,
    updateProgress,
    clearError,
  };
}
