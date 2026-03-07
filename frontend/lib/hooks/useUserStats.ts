/**
 * User Statistics Hook
 * 
 * Fetches and manages user statistics from the backend including:
 * - Current streak
 * - Longest streak
 * - Overall completion percentage
 * - Completed content count
 * 
 * Note: Users must be authenticated to access pages that use this hook.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient, UserStatsResponse } from '@/lib/api';
import { onProgressUpdate } from '@/lib/events';

/**
 * User stats state interface
 */
interface UserStatsState {
  currentStreak: number;
  longestStreak: number;
  overallCompletion: number;
  completedCount: number;
  quizzesPassed: number;
  walkthroughsCompleted: number;
  isLoading: boolean;
  error: string | null;
}

/**
 * User stats hook return type
 */
interface UseUserStatsReturn extends UserStatsState {
  refetch: () => Promise<void>;
  clearError: () => void;
}

/**
 * useUserStats Hook
 * 
 * Fetches user statistics from backend or calculates from localStorage.
 * 
 * @returns User statistics state and methods
 */
export function useUserStats(): UseUserStatsReturn {
  const [state, setState] = useState<UserStatsState>({
    currentStreak: 0,
    longestStreak: 0,
    overallCompletion: 0,
    completedCount: 0,
    quizzesPassed: 0,
    walkthroughsCompleted: 0,
    isLoading: true,
    error: null,
  });

  /**
   * Fetch stats from backend
   */
  const fetchStats = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const { data, error } = await apiClient.getStats();

      if (data) {
        // Backend returns zeros for new users - this is expected and valid
        setState({
          currentStreak: data.current_streak,
          longestStreak: data.longest_streak,
          overallCompletion: data.overall_completion,
          completedCount: data.completed_count,
          quizzesPassed: data.quizzes_passed,
          walkthroughsCompleted: data.walkthroughs_completed,
          isLoading: false,
          error: null,
        });
      } else {
        // Return empty stats on error
        setState({
          currentStreak: 0,
          longestStreak: 0,
          overallCompletion: 0,
          completedCount: 0,
          quizzesPassed: 0,
          walkthroughsCompleted: 0,
          isLoading: false,
          error: error || 'Failed to fetch statistics',
        });
      }
    } catch (error) {
      // Return empty stats on exception
      setState({
        currentStreak: 0,
        longestStreak: 0,
        overallCompletion: 0,
        completedCount: 0,
        quizzesPassed: 0,
        walkthroughsCompleted: 0,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Network error',
      });
    }
  }, []);

  /**
   * Fetch stats on mount and when authentication changes
   */
  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  /**
   * Listen for progress update events and refetch
   */
  useEffect(() => {
    const cleanup = onProgressUpdate(() => {
      fetchStats();
    });
    
    return cleanup;
  }, [fetchStats]);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    ...state,
    refetch: fetchStats,
    clearError,
  };
}
