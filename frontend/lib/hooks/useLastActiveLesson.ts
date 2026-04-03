/**
 * Last Active Lesson Hook
 *
 * Fetches the learner's last active lesson from the backend on mount.
 * Used by the Dashboard to determine the "Continue Learning" resume point.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api';

interface LastActiveLessonState {
  pageId: string | null;
  pageSlug: string | null;
  isLoading: boolean;
}

export function useLastActiveLesson(): LastActiveLessonState {
  const [state, setState] = useState<LastActiveLessonState>({
    pageId: null,
    pageSlug: null,
    isLoading: true,
  });

  const fetchLastActiveLesson = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true }));

    try {
      const { data } = await apiClient.getLastActiveLesson();

      if (data) {
        setState({
          pageId: data.page_id,
          pageSlug: data.page_slug,
          isLoading: false,
        });
      } else {
        setState({
          pageId: null,
          pageSlug: null,
          isLoading: false,
        });
      }
    } catch {
      setState({
        pageId: null,
        pageSlug: null,
        isLoading: false,
      });
    }
  }, []);

  useEffect(() => {
    fetchLastActiveLesson();
  }, [fetchLastActiveLesson]);

  return state;
}
