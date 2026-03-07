/**
 * Badges Hook
 * 
 * Fetches and manages user badges from the backend.
 * Shows which badges are earned and which are locked.
 * Detects newly earned badges and triggers notifications.
 * Note: Users must be authenticated to access pages that use this hook.
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { apiClient, BadgeData } from '@/lib/api';
import { Badge } from '@/lib/types';

/**
 * Badges state interface
 */
interface BadgesState {
  badges: Badge[];
  isLoading: boolean;
  error: string | null;
  newlyEarnedBadges: Badge[];
}

/**
 * Badges hook return type
 */
interface UseBadgesReturn extends BadgesState {
  refetch: () => Promise<void>;
  clearError: () => void;
  clearNewBadge: () => void;
}

/**
 * Transform backend badge data to frontend Badge type
 */
function transformBadgeData(backendBadges: BadgeData[]): Badge[] {
  return backendBadges.map(badge => ({
    id: badge.id,
    title: badge.title,
    description: badge.description,
    icon: badge.icon,
    earned: badge.earned,
    earnedDate: badge.earned_date,
  }));
}

/**
 * Default badges for unauthenticated users (all locked)
 */
const DEFAULT_BADGES: Badge[] = [
  {
    id: 'b1',
    title: 'First Steps',
    description: 'Complete your first lesson',
    icon: '🎯',
    earned: false,
  },
  {
    id: 'b2',
    title: 'DevSecOps Guru',
    description: 'Complete DevSecOps path',
    icon: '🛡️',
    earned: false,
  },
  {
    id: 'b3',
    title: 'Cloud Security Developer',
    description: 'Complete Cloud Security Development path',
    icon: '☁️',
    earned: false,
  },
  {
    id: 'b4',
    title: 'Walkthrough Newbie',
    description: 'Complete beginner walkthrough',
    icon: '🌱',
    earned: false,
  },
  {
    id: 'b5',
    title: 'Walkthrough Pro',
    description: 'Complete intermediate walkthrough',
    icon: '⚡',
    earned: false,
  },
  {
    id: 'b6',
    title: 'Walkthrough Expert',
    description: 'Complete expert level walkthrough',
    icon: '🏆',
    earned: false,
  },
];

/**
 * Get badge IDs from localStorage
 */
function getStoredBadgeIds(): string[] {
  if (typeof window === 'undefined') return [];
  try {
    const stored = localStorage.getItem('earnedBadgeIds');
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

/**
 * Store badge IDs in localStorage
 */
function storeBadgeIds(badgeIds: string[]): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem('earnedBadgeIds', JSON.stringify(badgeIds));
  } catch {
    // Ignore storage errors
  }
}

/**
 * useBadges Hook
 * 
 * Fetches user badges from backend or returns default locked badges.
 * Detects newly earned badges by comparing with previously stored badge IDs.
 * 
 * @returns Badges state and methods
 */
export function useBadges(): UseBadgesReturn {
  const [state, setState] = useState<BadgesState>({
    badges: DEFAULT_BADGES,
    isLoading: true,
    error: null,
    newlyEarnedBadges: [],
  });

  // Track previous badge IDs to detect new badges
  const previousBadgeIdsRef = useRef<string[]>([]);
  const isInitialLoadRef = useRef(true);

  /**
   * Fetch badges from backend
   */
  const fetchBadges = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const { data, error } = await apiClient.getBadges();

      if (data) {
        const badges = transformBadgeData(data.badges);
        const earnedBadgeIds = badges.filter(b => b.earned).map(b => b.id);
        
        // Detect newly earned badges (multiple)
        let newlyEarnedBadges: Badge[] = [];
        
        if (!isInitialLoadRef.current) {
          // Not the first load - check for new badges
          const previousIds = previousBadgeIdsRef.current;
          const newBadgeIds = earnedBadgeIds.filter(id => !previousIds.includes(id));
          
          if (newBadgeIds.length > 0) {
            newlyEarnedBadges = badges.filter(b => newBadgeIds.includes(b.id));
          }
        } else {
          // First load - initialize from localStorage
          const storedIds = getStoredBadgeIds();
          previousBadgeIdsRef.current = storedIds;
          
          // Check if there are new badges since last session
          const newBadgeIds = earnedBadgeIds.filter(id => !storedIds.includes(id));
          if (newBadgeIds.length > 0) {
            newlyEarnedBadges = badges.filter(b => newBadgeIds.includes(b.id));
          }
          
          isInitialLoadRef.current = false;
        }
        
        // Update stored badge IDs
        previousBadgeIdsRef.current = earnedBadgeIds;
        storeBadgeIds(earnedBadgeIds);
        
        setState({
          badges,
          isLoading: false,
          error: null,
          newlyEarnedBadges,
        });
      } else {
        // Return default badges on error
        setState({
          badges: DEFAULT_BADGES,
          isLoading: false,
          error: error || 'Failed to fetch badges',
          newlyEarnedBadges: [],
        });
      }
    } catch (error) {
      // Return default badges on exception
      setState({
        badges: DEFAULT_BADGES,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Network error',
        newlyEarnedBadges: [],
      });
    }
  }, []);

  /**
   * Fetch badges on mount and when authentication changes
   * Also listen for badge check events
   */
  useEffect(() => {
    fetchBadges();
    
    // Listen for badge check events
    const handleBadgeCheck = () => {
      fetchBadges();
    };
    
    if (typeof window !== 'undefined') {
      window.addEventListener('badge:check', handleBadgeCheck);
      
      return () => {
        window.removeEventListener('badge:check', handleBadgeCheck);
      };
    }
  }, [fetchBadges]);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  /**
   * Clear the first newly earned badge from the queue
   */
  const clearNewBadge = useCallback(() => {
    setState(prev => ({ 
      ...prev, 
      newlyEarnedBadges: prev.newlyEarnedBadges.slice(1) 
    }));
  }, []);

  return {
    ...state,
    refetch: fetchBadges,
    clearError,
    clearNewBadge,
  };
}
