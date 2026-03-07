/**
 * Recent Activities Hook
 * 
 * Fetches recently completed content from the backend.
 * Note: Users must be authenticated to access pages that use this hook.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient, ProgressItem } from '@/lib/api';
import modulesData from '@/lib/data/modules.json';
import { onProgressUpdate } from '@/lib/events';

/**
 * Activity with formatted display data
 */
export interface Activity {
  id: string;
  contentId: string;
  title: string;
  path: string;
  completedAt: string;
  relativeTime: string;
}

/**
 * Recent activities state interface
 */
interface RecentActivitiesState {
  activities: Activity[];
  isLoading: boolean;
  error: string | null;
}

/**
 * Recent activities hook return type
 */
interface UseRecentActivitiesReturn extends RecentActivitiesState {
  refetch: () => Promise<void>;
  clearError: () => void;
}

/**
 * Find page and module metadata from modules.json by content_id
 * Content ID format: "know_before_you_go/prerequisites/module_1"
 */
function findPageMetadata(contentId: string): { title: string; description: string } | null {
  const allModules = modulesData as any[];
  
  // First try to match by page.id
  for (const module of allModules) {
    for (const page of module.pages) {
      if (page.id === contentId) {
        return {
          title: page.title,
          description: module.title // Use module title (e.g., "Prerequisites") as description
        };
      }
    }
  }
  
  // If not found, try to match by slug path
  // Convert content_id to slug format: "know_before_you_go/prerequisites/module_1" -> "/learn/know_before_you_go/prerequisites/module_1"
  const slugToMatch = `/learn/${contentId}`;
  
  for (const module of allModules) {
    for (const page of module.pages) {
      if (page.slug === slugToMatch) {
        return {
          title: page.title,
          description: module.title // Use module title (e.g., "Prerequisites") as description
        };
      }
    }
  }
  
  // If still not found, try without the last segment (for quiz/capstone pages)
  const parts = contentId.split('/');
  if (parts.length > 2) {
    const moduleId = parts.slice(0, 2).join('/'); // e.g., "know_before_you_go/prerequisites"
    for (const module of allModules) {
      if (module.id === moduleId) {
        return {
          title: parts[parts.length - 1].replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
          description: module.title
        };
      }
    }
  }
  
  return null;
}

/**
 * Format content_id to display title and path
 * Uses modules.json for accurate titles, falls back to slug formatting
 */
function formatContentId(contentId: string): { title: string; path: string } {
  // Special handling for capstone submissions (hyphenated format)
  // Convert "devsecops-capstone" to "devsecops/capstone"
  if (contentId.includes('-capstone')) {
    const normalizedId = contentId.replace('-capstone', '/capstone');
    const metadata = findPageMetadata(normalizedId);
    if (metadata) {
      return {
        title: metadata.title,
        path: metadata.description
      };
    }
  }
  
  // Try to find in modules.json first
  const metadata = findPageMetadata(contentId);
  if (metadata) {
    return {
      title: metadata.title,
      path: metadata.description // Use module title as the subtitle
    };
  }
  
  // For old format entries (just page name like "module_1" or "welcome"),
  // try to find by searching all pages
  const allModules = modulesData as any[];
  for (const module of allModules) {
    for (const page of module.pages) {
      // Check if the slug ends with the content_id (for old format)
      if (page.slug.endsWith(`/${contentId}`) || page.slug === `/learn/${contentId}`) {
        return {
          title: page.title,
          path: module.title
        };
      }
    }
  }
  
  // Fallback to slug formatting if not found
  const parts = contentId.split('/');
  
  if (parts.length === 0) {
    return { title: 'Unknown', path: 'Unknown' };
  }

  // Get the last part as title
  const titleSlug = parts[parts.length - 1];
  const title = titleSlug
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');

  // Get the first part as path (or use title if only one part)
  const pathSlug = parts.length > 1 ? parts[0] : titleSlug;
  const path = pathSlug
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');

  return { title, path };
}

/**
 * Calculate relative time from ISO timestamp
 */
function getRelativeTime(isoTimestamp: string): string {
  try {
    const date = new Date(isoTimestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString();
  } catch {
    return 'Recently';
  }
}

/**
 * Transform backend progress items to display activities
 * Deduplicates by normalized content_id AND title, keeping only the most recent completion
 */
function transformProgressItems(items: ProgressItem[]): Activity[] {
  // First pass: deduplicate by normalized content_id
  const uniqueByContentId = new Map<string, ProgressItem>();
  
  items.forEach(item => {
    // Normalize content_id to lowercase for deduplication
    const normalizedId = item.content_id.toLowerCase().replace(/[_\s]/g, '-');
    const existing = uniqueByContentId.get(normalizedId);
    
    if (!existing || new Date(item.completed_at) > new Date(existing.completed_at)) {
      uniqueByContentId.set(normalizedId, item);
    }
  });
  
  // Second pass: deduplicate by title (in case content_ids are different but refer to same page)
  const uniqueByTitle = new Map<string, ProgressItem>();
  
  Array.from(uniqueByContentId.values()).forEach(item => {
    const { title } = formatContentId(item.content_id);
    const normalizedTitle = title.toLowerCase();
    const existing = uniqueByTitle.get(normalizedTitle);
    
    if (!existing || new Date(item.completed_at) > new Date(existing.completed_at)) {
      uniqueByTitle.set(normalizedTitle, item);
    }
  });
  
  // Convert map back to array and transform
  return Array.from(uniqueByTitle.values()).map((item) => {
    const { title, path } = formatContentId(item.content_id);
    return {
      id: item.content_id,
      contentId: item.content_id,
      title,
      path,
      completedAt: item.completed_at,
      relativeTime: getRelativeTime(item.completed_at),
    };
  });
}

/**
 * useRecentActivities Hook
 * 
 * Fetches and formats recent activities from backend.
 * 
 * @returns Recent activities state and methods
 */
export function useRecentActivities(): UseRecentActivitiesReturn {
  const [state, setState] = useState<RecentActivitiesState>({
    activities: [],
    isLoading: true,
    error: null,
  });

  /**
   * Fetch recent activities from backend
   */
  const fetchActivities = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const { data, error } = await apiClient.getRecentActivities();

      if (data) {
        // Empty array for new users is valid - transform to activities
        const activities = transformProgressItems(data.recent);
        setState({
          activities,
          isLoading: false,
          error: null,
        });
      } else {
        // Empty activities on error - don't show error for new users
        setState({
          activities: [],
          isLoading: false,
          error: error || 'Failed to fetch recent activities',
        });
      }
    } catch (error) {
      // Empty activities on exception
      setState({
        activities: [],
        isLoading: false,
        error: error instanceof Error ? error.message : 'Network error',
      });
    }
  }, []);

  /**
   * Fetch activities on mount and when authentication changes
   */
  useEffect(() => {
    fetchActivities();
  }, [fetchActivities]);

  /**
   * Listen for progress update events and refetch
   */
  useEffect(() => {
    const cleanup = onProgressUpdate(() => {
      fetchActivities();
    });
    
    return cleanup;
  }, [fetchActivities]);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    ...state,
    refetch: fetchActivities,
    clearError,
  };
}
