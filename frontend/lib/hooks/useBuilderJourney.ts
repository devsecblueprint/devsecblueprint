/**
 * Builder Journey Hook
 *
 * Fetches and manages Builder Journey progress state from the backend.
 * Provides task completion mutations with optimistic updates and
 * analytics event emission. Supports both Free and Builder tiers.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { trackJourneyEvent } from '@/lib/utils/journey-analytics';
import {
  BUILDER_JOURNEY_PHASES,
  BUILDER_JOURNEY_TOTAL_TASKS,
  FREE_JOURNEY_PHASES,
  FREE_JOURNEY_TOTAL_TASKS,
} from '@/lib/data/builder-journey';
import type { BuilderJourneyPhase, BuilderJourneyTask, JourneyTier } from '@/lib/data/builder-journey';

/**
 * Status of a single journey task
 */
export interface JourneyTaskStatus {
  taskId: string;
  status: 'not_started' | 'in_progress' | 'completed';
  completedAt?: string;
}

/**
 * API response shape for GET /progress/journey
 */
interface JourneyProgressApiResponse {
  tasks: Array<{
    task_id: string;
    phase: number;
    status: string;
    completed_at: string | null;
    auto_completed: boolean;
  }>;
  current_phase: number;
  completion_percentage: number;
  is_complete: boolean;
  journey_started_at: string | null;
  tier: string | null;
}

/**
 * API response shape for PUT /progress/journey
 */
interface CompleteTaskApiResponse {
  task_id: string;
  status: string;
  completed_at: string;
  phase_completed: boolean;
  journey_completed: boolean;
}

/**
 * Return type for the useBuilderJourney hook
 */
export interface UseBuilderJourneyReturn {
  /** All task statuses keyed by task ID */
  taskStatuses: Record<string, JourneyTaskStatus>;
  /** Current active phase (1-5) */
  currentPhase: number;
  /** Overall completion percentage (0-100) */
  completionPercentage: number;
  /** The single next recommended task */
  recommendedAction: (BuilderJourneyTask & { phaseTitle: string }) | null;
  /** Recently completed tasks (most recent first, max 3) */
  recentCompletions: (JourneyTaskStatus & { title: string })[];
  /** Whether the entire journey is complete */
  isComplete: boolean;
  /** Loading state */
  isLoading: boolean;
  /** Error state */
  error: string | null;
  /** Whether the user is not eligible (e.g. 403 response) */
  notEligible: boolean;
  /** The user's journey tier */
  tier: JourneyTier | null;
  /** Mark a task as complete */
  completeTask: (taskId: string) => Promise<void>;
  /** Refresh journey state */
  refetch: () => Promise<void>;
}

/**
 * Compute the recommended next action from task statuses.
 * Returns the first incomplete task in the lowest incomplete phase.
 */
function computeRecommendedAction(
  taskStatuses: Record<string, JourneyTaskStatus>,
  phases: BuilderJourneyPhase[]
): (BuilderJourneyTask & { phaseTitle: string }) | null {
  for (const phase of phases) {
    for (const task of phase.tasks) {
      const status = taskStatuses[task.id];
      if (!status || status.status !== 'completed') {
        return { ...task, phaseTitle: phase.title };
      }
    }
  }
  return null;
}

/**
 * Compute recent completions from task statuses (most recent first, max 3).
 */
function computeRecentCompletions(
  taskStatuses: Record<string, JourneyTaskStatus>,
  phases: BuilderJourneyPhase[]
): (JourneyTaskStatus & { title: string })[] {
  // Build a lookup for task titles
  const titleMap: Record<string, string> = {};
  for (const phase of phases) {
    for (const task of phase.tasks) {
      titleMap[task.id] = task.title;
    }
  }

  const completed = Object.values(taskStatuses)
    .filter((ts) => ts.status === 'completed' && ts.completedAt)
    .sort((a, b) => {
      const dateA = a.completedAt ? new Date(a.completedAt).getTime() : 0;
      const dateB = b.completedAt ? new Date(b.completedAt).getTime() : 0;
      return dateB - dateA;
    })
    .slice(0, 3)
    .map((ts) => ({
      ...ts,
      title: titleMap[ts.taskId] || ts.taskId,
    }));

  return completed;
}

/**
 * Determine the current phase from task statuses.
 * The current phase is the lowest phase with at least one incomplete task.
 */
function computeCurrentPhase(
  taskStatuses: Record<string, JourneyTaskStatus>,
  phases: BuilderJourneyPhase[]
): number {
  for (const phase of phases) {
    const hasIncomplete = phase.tasks.some((task) => {
      const status = taskStatuses[task.id];
      return !status || status.status !== 'completed';
    });
    if (hasIncomplete) {
      return phase.phase;
    }
  }
  // All complete — return last phase
  return phases[phases.length - 1].phase;
}

/**
 * Compute completion percentage from task statuses.
 */
function computeCompletionPercentage(
  taskStatuses: Record<string, JourneyTaskStatus>,
  totalTasks: number
): number {
  const completedCount = Object.values(taskStatuses).filter(
    (ts) => ts.status === 'completed'
  ).length;
  if (totalTasks === 0) return 0;
  return Math.round((completedCount / totalTasks) * 100);
}

/**
 * Find the phase number for a given task ID.
 */
function getPhaseForTask(taskId: string, phases: BuilderJourneyPhase[]): number {
  for (const phase of phases) {
    if (phase.tasks.some((t) => t.id === taskId)) {
      return phase.phase;
    }
  }
  return 1;
}

/**
 * useBuilderJourney Hook
 *
 * Fetches Builder Journey progress state and provides task completion
 * mutations with optimistic local updates and analytics events.
 * Supports both Free and Builder tiers based on API response.
 *
 * @returns Journey state and methods
 */
export function useBuilderJourney(): UseBuilderJourneyReturn {
  const [taskStatuses, setTaskStatuses] = useState<Record<string, JourneyTaskStatus>>({});
  const [isComplete, setIsComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notEligible, setNotEligible] = useState(false);
  const [tier, setTier] = useState<JourneyTier | null>(null);

  /**
   * Get the appropriate phases and total tasks based on tier
   */
  const getPhases = useCallback((): BuilderJourneyPhase[] => {
    if (tier === 'FREE') return FREE_JOURNEY_PHASES;
    return BUILDER_JOURNEY_PHASES;
  }, [tier]);

  const getTotalTasks = useCallback((): number => {
    if (tier === 'FREE') return FREE_JOURNEY_TOTAL_TASKS;
    return BUILDER_JOURNEY_TOTAL_TASKS;
  }, [tier]);

  /**
   * Fetch journey progress from the backend
   */
  const fetchJourney = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const { data, error: apiError, statusCode } = await apiClient.get<JourneyProgressApiResponse>(
        '/progress/journey'
      );

      // Handle 403 — user is truly not eligible (unauthenticated edge case)
      if (statusCode === 403) {
        setNotEligible(true);
        setIsLoading(false);
        return;
      }

      if (data) {
        // Set tier from API response
        const responseTier = (data.tier as JourneyTier) || 'FREE';
        setTier(responseTier);

        // Parse response into task statuses map
        const statuses: Record<string, JourneyTaskStatus> = {};
        for (const item of data.tasks) {
          statuses[item.task_id] = {
            taskId: item.task_id,
            status: item.status as JourneyTaskStatus['status'],
            completedAt: item.completed_at || undefined,
          };
        }

        setTaskStatuses(statuses);
        setIsComplete(data.is_complete);
        setNotEligible(false);
        setIsLoading(false);

        if (data.journey_started_at) {
          trackJourneyEvent({ type: 'journey_started', userId: '', tier: responseTier });
        }
      } else {
        setError(apiError || 'Failed to fetch journey progress');
        setIsLoading(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Network error');
      setIsLoading(false);
    }
  }, []);

  /**
   * Fetch on mount
   */
  useEffect(() => {
    fetchJourney();
  }, [fetchJourney]);

  /**
   * Complete a task via PUT /progress/journey
   * Optimistically updates local state.
   */
  const completeTask = useCallback(
    async (taskId: string) => {
      const previousStatuses = { ...taskStatuses };
      const now = new Date().toISOString();
      const phases = getPhases();
      const phaseId = getPhaseForTask(taskId, phases);
      const currentTier = tier || 'FREE';

      // Optimistic update
      setTaskStatuses((prev) => ({
        ...prev,
        [taskId]: {
          taskId,
          status: 'completed',
          completedAt: now,
        },
      }));

      try {
        const { data, error: apiError } = await apiClient.put<CompleteTaskApiResponse>(
          '/progress/journey',
          { task_id: taskId }
        );

        if (data) {
          // Emit task_completed analytics event
          trackJourneyEvent({
            type: 'task_completed',
            taskId,
            phaseId,
            timestamp: data.completed_at,
            tier: currentTier,
          });

          // Check if phase was completed
          if (data.phase_completed) {
            trackJourneyEvent({
              type: 'phase_completed',
              phaseId,
              durationDays: 0, // Duration not available in PUT response
              tier: currentTier,
            });
          }

          // Check if entire journey was completed
          if (data.journey_completed) {
            setIsComplete(true);
            trackJourneyEvent({
              type: 'journey_completed',
              totalDurationDays: 0, // Duration not available in PUT response
              tier: currentTier,
            });
          }
        } else {
          // Revert optimistic update on failure
          setTaskStatuses(previousStatuses);
          setError(apiError || 'Failed to complete task');
        }
      } catch (err) {
        // Revert optimistic update on error
        setTaskStatuses(previousStatuses);
        setError(err instanceof Error ? err.message : 'Network error');
      }
    },
    [taskStatuses, tier, getPhases]
  );

  // Derived state using tier-appropriate phases
  const phases = getPhases();
  const totalTasks = getTotalTasks();
  const currentPhase = computeCurrentPhase(taskStatuses, phases);
  const completionPercentage = computeCompletionPercentage(taskStatuses, totalTasks);
  const recommendedAction = computeRecommendedAction(taskStatuses, phases);
  const recentCompletions = computeRecentCompletions(taskStatuses, phases);

  return {
    taskStatuses,
    currentPhase,
    completionPercentage,
    recommendedAction,
    recentCompletions,
    isComplete,
    isLoading,
    error,
    notEligible,
    tier,
    completeTask,
    refetch: fetchJourney,
  };
}
