'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { useBuilderJourney } from '@/lib/hooks/useBuilderJourney';
import {
  BUILDER_JOURNEY_PHASES,
  FREE_JOURNEY_PHASES,
} from '@/lib/data/builder-journey';

/**
 * BuilderJourneyWidget
 *
 * Dashboard widget displaying the authenticated user's journey progress.
 * Shows current phase, overall progress bar, recommended next action,
 * recently completed milestones, and expandable task list for current phase.
 *
 * Renders nothing when the journey is complete or user is not eligible (403).
 * Supports both Free and Builder tiers with tier-conditional title.
 *
 * Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 5.1, 5.2, 5.3, 5.5, 5.6, 5.7, 6.1, 6.3, 6.4, 6.5, 10.2, 10.3, 10.4, 10.5
 */
export function BuilderJourneyWidget() {
  const {
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
  } = useBuilderJourney();

  const [expanded, setExpanded] = useState(false);

  // Don't render for truly ineligible users (403)
  if (notEligible) {
    return null;
  }

  // Don't render when journey is complete
  if (!isLoading && isComplete) {
    return null;
  }

  // Determine the widget title based on tier
  const widgetTitle = tier === 'FREE' ? 'Your Journey' : 'Your Builder Journey';

  // Select tier-appropriate phases for the expandable task list
  const phases = tier === 'FREE' ? FREE_JOURNEY_PHASES : BUILDER_JOURNEY_PHASES;

  // Skeleton loading state
  if (isLoading) {
    return (
      <section className="w-full" aria-label="Builder Journey progress loading">
        <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
          Your Builder Journey
        </h2>
        <Card padding="lg">
          <div className="animate-pulse space-y-4 py-2">
            <div className="h-4 w-32 bg-gray-200 dark:bg-gray-800 rounded" />
            <div className="h-6 w-48 bg-gray-200 dark:bg-gray-800 rounded" />
            <div className="h-3 w-full max-w-md bg-gray-200 dark:bg-gray-800 rounded-full" />
            <div className="h-4 w-64 bg-gray-200 dark:bg-gray-800 rounded" />
            <div className="space-y-2 pt-2">
              <div className="h-4 w-56 bg-gray-200 dark:bg-gray-800 rounded" />
              <div className="h-4 w-44 bg-gray-200 dark:bg-gray-800 rounded" />
              <div className="h-4 w-52 bg-gray-200 dark:bg-gray-800 rounded" />
            </div>
          </div>
        </Card>
      </section>
    );
  }

  // Error state
  if (error) {
    return (
      <section className="w-full" aria-label="Builder Journey progress error">
        <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
          {widgetTitle}
        </h2>
        <Card padding="lg">
          <div className="text-center py-6">
            <p className="text-gray-600 dark:text-gray-400 mb-3">
              Unable to load your journey progress.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="inline-flex items-center px-4 py-2 bg-amber-500 dark:bg-amber-400 text-gray-900 font-medium rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
            >
              Retry
            </button>
          </div>
        </Card>
      </section>
    );
  }

  // Get current phase data from tier-appropriate phases
  const currentPhaseData = phases.find(
    (p) => p.phase === currentPhase
  );

  return (
    <section className="w-full" aria-label="Builder Journey progress">
      <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
        {widgetTitle}
      </h2>
      <Card padding="lg">
        <div className="space-y-5">
          {/* Phase indicator and progress */}
          <div>
            <p className="text-sm font-medium text-amber-600 dark:text-amber-400 mb-1">
              Phase {currentPhase} of {phases.length}
            </p>
            <h3 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-gray-100">
              {currentPhaseData?.title || `Phase ${currentPhase}`}
            </h3>
          </div>

          {/* Overall progress bar */}
          <div>
            <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
              <span>Overall Progress</span>
              <span>{completionPercentage}%</span>
            </div>
            <ProgressBar percentage={completionPercentage} height="sm" />
          </div>

          {/* Recommended next action */}
          {recommendedAction && (
            <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
              <p className="text-xs font-medium text-amber-700 dark:text-amber-300 uppercase tracking-wide mb-1">
                Recommended Next
              </p>
              <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                {recommendedAction.title}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                {recommendedAction.description}
              </p>
            </div>
          )}

          {/* Recent completions */}
          {recentCompletions.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
                Recently Completed
              </p>
              <ul className="space-y-1.5">
                {recentCompletions.map((item) => (
                  <li
                    key={item.taskId}
                    className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300"
                  >
                    <svg
                      className="w-4 h-4 text-green-500 dark:text-green-400 shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    <span className="truncate">{item.title}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Expandable current phase tasks */}
          {currentPhaseData && (
            <div className="border-t border-gray-200 dark:border-gray-800 pt-4">
              <button
                onClick={() => setExpanded(!expanded)}
                className="flex items-center justify-between w-full text-left min-h-[44px] px-1 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
                aria-expanded={expanded}
                aria-controls="journey-phase-tasks"
              >
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {expanded ? 'Hide' : 'View'} Phase {currentPhase} Tasks
                </span>
                <svg
                  className={`w-5 h-5 text-gray-500 dark:text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>

              {expanded && (
                <ul
                  id="journey-phase-tasks"
                  className="mt-2 space-y-2"
                  role="list"
                >
                  {currentPhaseData.tasks.map((task) => {
                    const status = taskStatuses[task.id];
                    const isCompleted = status?.status === 'completed';

                    return (
                      <li key={task.id} className="flex items-start gap-3">
                        <label className="flex items-start gap-3 cursor-pointer w-full min-h-[44px] py-1">
                          <input
                            type="checkbox"
                            checked={isCompleted}
                            disabled={isCompleted}
                            onChange={() => {
                              if (!isCompleted) {
                                completeTask(task.id);
                              }
                            }}
                            className="mt-0.5 h-5 w-5 shrink-0 rounded border-gray-300 dark:border-gray-600 text-amber-500 focus:ring-amber-500 dark:bg-gray-800 disabled:opacity-60"
                            aria-label={`Mark "${task.title}" as complete`}
                          />
                          <span
                            className={`text-sm ${
                              isCompleted
                                ? 'text-gray-400 dark:text-gray-500 line-through'
                                : 'text-gray-700 dark:text-gray-300'
                            }`}
                          >
                            {task.title}
                          </span>
                        </label>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          )}
        </div>
      </Card>
    </section>
  );
}
