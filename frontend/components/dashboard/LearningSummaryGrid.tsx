'use client';

import { useUserStats } from '@/lib/hooks/useUserStats';
import { Card } from '@/components/ui/Card';
import { ProgressRing } from '@/components/dashboard/ProgressRing';
import { SkeletonStatCard } from '@/components/ui/Skeleton';

/**
 * LearningSummaryGrid Component
 *
 * Displays 4 metric cards in a responsive grid:
 * - Overall Completion (with ProgressRing)
 * - Quizzes Passed
 * - Walkthroughs Completed
 * - Current Streak (with longest streak)
 *
 * Calls useUserStats() internally. Shows skeleton cards while loading
 * and zero values on error without displaying error messages.
 *
 * Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 9.1, 10.2, 10.3
 */
export function LearningSummaryGrid() {
  const {
    currentStreak,
    longestStreak,
    overallCompletion,
    quizzesPassed,
    walkthroughsCompleted,
    isLoading,
  } = useUserStats();

  return (
    <section aria-labelledby="learning-summary-heading">
      <h2
        id="learning-summary-heading"
        className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6"
      >
        Learning Summary
      </h2>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonStatCard key={i} />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Overall Completion */}
          <Card className="flex flex-col items-center text-center">
            <ProgressRing
              percentage={overallCompletion}
              size={80}
              strokeWidth={8}
              className="mb-3"
            />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Overall Completion
            </span>
            <span className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              Total progress across all courses
            </span>
          </Card>

          {/* Quizzes Passed */}
          <Card className="flex flex-col items-center text-center">
            <span className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              {quizzesPassed}
            </span>
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Quizzes Passed
            </span>
            <span className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              Knowledge checks completed
            </span>
          </Card>

          {/* Walkthroughs Completed */}
          <Card className="flex flex-col items-center text-center">
            <span className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              {walkthroughsCompleted}
            </span>
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Walkthroughs Completed
            </span>
            <span className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              Hands-on exercises finished
            </span>
          </Card>

          {/* Current Streak */}
          <Card className="flex flex-col items-center text-center">
            <span className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              {currentStreak} {currentStreak === 1 ? 'day' : 'days'}
            </span>
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Current Streak
            </span>
            <span className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              Longest: {longestStreak} {longestStreak === 1 ? 'day' : 'days'}
            </span>
          </Card>
        </div>
      )}
    </section>
  );
}
