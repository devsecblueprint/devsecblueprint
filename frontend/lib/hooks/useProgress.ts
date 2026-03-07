/**
 * Progress Tracking Hook
 * 
 * Provides progress tracking functionality with backend integration.
 * Note: Users must be authenticated to access pages that use this hook.
 * 
 * Usage:
 * ```typescript
 * import { useProgress } from '@/lib/hooks/useProgress';
 * 
 * function LearningPage() {
 *   const { saveProgress, isSaving, error } = useProgress();
 *   
 *   const handleNext = async () => {
 *     const success = await saveProgress('page-id');
 *     if (success) {
 *       // Navigate to next page
 *     }
 *   };
 *   
 *   return <button onClick={handleNext} disabled={isSaving}>Next</button>;
 * }
 * ```
 */

'use client';

import { useState, useCallback } from 'react';
import { apiClient } from '@/lib/api';

/**
 * Progress state interface
 */
interface ProgressState {
  isSaving: boolean;
  error: string | null;
  lastSaved: string | null;
}

/**
 * Progress hook return type
 */
interface UseProgressReturn extends ProgressState {
  saveProgress: (contentId: string) => Promise<boolean>;
  clearError: () => void;
}

/**
 * useProgress Hook
 * 
 * Manages progress tracking with backend integration.
 * 
 * @returns Progress state and methods
 */
export function useProgress(): UseProgressReturn {
  const [state, setState] = useState<ProgressState>({
    isSaving: false,
    error: null,
    lastSaved: null,
  });

  /**
   * Save progress to backend
   * 
   * @param contentId - Content identifier
   * @returns Promise resolving to success status
   */
  const saveProgress = useCallback(async (contentId: string): Promise<boolean> => {
    // Validate contentId
    if (!contentId || typeof contentId !== 'string') {
      setState(prev => ({
        ...prev,
        error: 'Invalid content ID',
      }));
      return false;
    }

    setState(prev => ({ ...prev, isSaving: true, error: null }));

    try {
      const { data, error } = await apiClient.saveProgress(contentId);

      if (data) {
        setState({
          isSaving: false,
          error: null,
          lastSaved: contentId,
        });
        
        return true;
      } else {
        setState({
          isSaving: false,
          error: error || 'Failed to save progress',
          lastSaved: null,
        });
        return false;
      }
    } catch (error) {
      setState({
        isSaving: false,
        error: error instanceof Error ? error.message : 'Network error',
        lastSaved: null,
      });
      return false;
    }
  }, []);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    ...state,
    saveProgress,
    clearError,
  };
}
