/**
 * Walkthrough Client - Combines local content with backend progress tracking
 * 
 * This module provides a unified interface for accessing walkthrough data:
 * - Content (metadata) is loaded from static data
 * - Progress tracking is handled via backend API
 */

import { apiClient } from '@/lib/api';
import { WALKTHROUGHS_DATA } from '@/lib/walkthroughs-data';
import type { 
  Walkthrough, 
  WalkthroughWithProgress, 
  WalkthroughFilters,
  WalkthroughProgress 
} from '@/lib/types';

/**
 * Fetch walkthroughs from static data with optional filtering
 */
function fetchWalkthroughs(filters?: WalkthroughFilters): Walkthrough[] {
  let walkthroughs = [...WALKTHROUGHS_DATA];
  
  // Apply difficulty filter
  if (filters?.difficulty) {
    walkthroughs = walkthroughs.filter(w => w.difficulty === filters.difficulty);
  }
  
  // Apply topics filter
  if (filters?.topics && filters.topics.length > 0) {
    walkthroughs = walkthroughs.filter(w => 
      filters.topics!.some(topic => w.topics.includes(topic))
    );
  }
  
  // Apply search filter
  if (filters?.search) {
    const searchLower = filters.search.toLowerCase();
    walkthroughs = walkthroughs.filter(w =>
      w.title.toLowerCase().includes(searchLower) ||
      w.description.toLowerCase().includes(searchLower) ||
      w.topics.some(topic => topic.toLowerCase().includes(searchLower))
    );
  }
  
  return walkthroughs;
}

/**
 * Get all walkthroughs with progress data
 * 
 * Loads walkthrough content from static data and enriches with
 * progress data from backend API (if authenticated)
 * 
 * @param filters - Optional filter criteria
 * @param includeProgress - Whether to fetch progress from backend (default: true)
 * @returns Array of walkthroughs with progress data
 */
export async function getWalkthroughsWithProgress(
  filters?: WalkthroughFilters,
  includeProgress: boolean = true
): Promise<WalkthroughWithProgress[]> {
  // Load all walkthroughs from static data
  const walkthroughs = fetchWalkthroughs(filters);
  
  // Enrich with progress data if requested
  if (includeProgress) {
    const walkthroughsWithProgress = await Promise.all(
      walkthroughs.map(async (walkthrough) => {
        const progress = await getWalkthroughProgressData(walkthrough.id);
        return {
          ...walkthrough,
          progress
        };
      })
    );
    
    // Apply status filter if provided (requires progress data)
    if (filters?.status) {
      return walkthroughsWithProgress.filter(
        w => w.progress.status === filters.status
      );
    }
    
    return walkthroughsWithProgress;
  }
  
  // Return without progress data
  return walkthroughs.map(w => ({
    ...w,
    progress: { status: 'not_started' as const }
  }));
}

/**
 * Get progress data for a walkthrough from backend API
 * 
 * @param id - Walkthrough identifier
 * @returns Progress data or default not_started status
 */
async function getWalkthroughProgressData(id: string): Promise<WalkthroughProgress> {
  try {
    const response = await apiClient.getWalkthroughProgress(id);
    
    if (response.data?.progress) {
      return {
        status: response.data.progress.status as 'not_started' | 'in_progress' | 'completed',
        startedAt: response.data.progress.started_at,
        completedAt: response.data.progress.completed_at
      };
    }
  } catch (error) {
    console.warn(`Failed to fetch progress for walkthrough ${id}:`, error);
  }
  
  // Default to not_started if API call fails or user not authenticated
  return { status: 'not_started' };
}

/**
 * Update walkthrough progress
 * 
 * @param id - Walkthrough identifier
 * @param status - New progress status
 * @returns Success status
 */
export async function updateWalkthroughProgress(
  id: string,
  status: 'in_progress' | 'completed'
): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await apiClient.updateWalkthroughProgress(id, status);
    
    if (response.error) {
      return { success: false, error: response.error };
    }
    
    return { success: true };
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Failed to update progress' 
    };
  }
}
