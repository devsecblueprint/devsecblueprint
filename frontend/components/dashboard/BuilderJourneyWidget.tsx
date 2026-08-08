'use client';

import { useState } from 'react';
import Link from 'next/link';
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
 * Tasks are rendered as clickable links that navigate to the relevant resource.
 * Completed tasks show a green check — no manual checkboxes.
 *
 * Renders nothing when the journey is complete or user is not eligible (403).
 * Supports both Free and Builder tiers with tier-conditional title.
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
  const widgetTitle = 'Your Onboarding Guide';

  // Select tier-appropriate phases for the expandable task list
  const phases = tier === 'FREE' ? FREE_JOURNEY_PHASES : BUILDER_JOURNEY_PHASES;

  // Skeleton loading state
  if (isLoading) {
    return (
      <section className="w-full" aria-label="Journey progress loading">
        <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
          Your Onboarding Guide
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
      <section className="w-full" aria-label="Journey progress error">
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
    <section className="w-full" aria-label="Journey progress">
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

          {/* Recommended next action — now a clickable link */}
          {recommendedAction && (
            <TaskActionLink
              actionUrl={recommendedAction.actionUrl}
              className="block bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg p-4 hover:bg-amber-100 dark:hover:bg-amber-950/50 transition-colors"
            >
              <p className="text-xs font-medium text-amber-700 dark:text-amber-300 uppercase tracking-wide mb-1">
                Recommended Next
              </p>
              <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                {recommendedAction.title}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                {recommendedAction.description}
              </p>
            </TaskActionLink>
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

          {/* Expandable current phase tasks — rendered as links, not checkboxes */}
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
                  className="mt-2 space-y-1"
                  role="list"
                >
                  {currentPhaseData.tasks.map((task) => {
                    const status = taskStatuses[task.id];
                    const isCompleted = status?.status === 'completed';
                    const isManualTask = !task.autoDetect;

                    return (
                      <li key={task.id}>
                        {isCompleted ? (
                          /* Completed tasks: show green check, non-interactive */
                          <div className="flex items-center gap-3 min-h-[44px] px-2 py-1.5 rounded-lg">
                            <svg
                              className="w-5 h-5 text-green-500 dark:text-green-400 shrink-0"
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
                            <span className="text-sm text-gray-400 dark:text-gray-500 line-through">
                              {task.title}
                            </span>
                          </div>
                        ) : isManualTask ? (
                          /* Manual tasks (Discord): link + check-off button */
                          <div className="flex items-center gap-2 min-h-[44px] px-2 py-1.5 rounded-lg">
                            <button
                              onClick={() => completeTask(task.id)}
                              className="w-5 h-5 shrink-0 rounded border-2 border-gray-300 dark:border-gray-600 hover:border-amber-500 dark:hover:border-amber-400 hover:bg-amber-50 dark:hover:bg-amber-950/30 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-1"
                              aria-label={`Mark "${task.title}" as done`}
                            />
                            <TaskActionLink
                              actionUrl={task.actionUrl}
                              className="flex-1 text-sm text-gray-700 dark:text-gray-300 hover:text-amber-600 dark:hover:text-amber-400 transition-colors"
                            >
                              {task.title}
                            </TaskActionLink>
                            <TaskActionLink
                              actionUrl={task.actionUrl}
                              className="shrink-0"
                            >
                              <svg
                                className="w-4 h-4 text-gray-400 dark:text-gray-600 hover:text-amber-500 dark:hover:text-amber-400 transition-colors"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                aria-hidden="true"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                                />
                              </svg>
                            </TaskActionLink>
                          </div>
                        ) : (
                          /* Auto-detect tasks: clickable link to the action */
                          <TaskActionLink
                            actionUrl={task.actionUrl}
                            className="flex items-center gap-3 min-h-[44px] px-2 py-1.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors group"
                          >
                            <span className="w-5 h-5 shrink-0 rounded-full border-2 border-gray-300 dark:border-gray-600 group-hover:border-amber-500 dark:group-hover:border-amber-400 transition-colors" />
                            <span className="text-sm text-gray-700 dark:text-gray-300 group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors">
                              {task.title}
                            </span>
                            <svg
                              className="w-4 h-4 ml-auto text-gray-400 dark:text-gray-600 group-hover:text-amber-500 dark:group-hover:text-amber-400 shrink-0 transition-colors"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                              aria-hidden="true"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M9 5l7 7-7 7"
                              />
                            </svg>
                          </TaskActionLink>
                        )}
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

/**
 * Renders either a Next.js Link (internal) or an anchor (external).
 * External URLs open in a new tab.
 */
function TaskActionLink({
  actionUrl,
  className,
  children,
}: {
  actionUrl: string;
  className?: string;
  children: React.ReactNode;
}) {
  const isExternal = actionUrl.startsWith('http');

  if (isExternal) {
    return (
      <a
        href={actionUrl}
        target="_blank"
        rel="noopener noreferrer"
        className={className}
      >
        {children}
      </a>
    );
  }

  return (
    <Link href={actionUrl} className={className}>
      {children}
    </Link>
  );
}
