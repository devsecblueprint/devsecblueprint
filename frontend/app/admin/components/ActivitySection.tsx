'use client';

import { useMemo } from 'react';
import { Card } from '@/components/ui/Card';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { Skeleton } from '@/components/ui/Skeleton';
import { useAdminContext } from './AdminDashboardProvider';
import { sortByCompletionDesc } from './utils';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Truncate a string to maxLen characters, adding ellipsis if exceeded. */
function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen) + '…';
}

// ---------------------------------------------------------------------------
// Loading Skeletons
// ---------------------------------------------------------------------------

function TopLearnersLoadingSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton className="h-4 w-24 flex-shrink-0" />
          <Skeleton className="h-3 flex-1" />
          <Skeleton className="h-4 w-10" />
        </div>
      ))}
    </div>
  );
}

function RecentMembersLoadingSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton className="h-4 w-28 flex-shrink-0" />
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-16" />
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Top Learners Sub-Component
// ---------------------------------------------------------------------------

interface TopLearnerItem {
  user_id: string;
  username: string;
  completed: number;
  percentage: number;
}

function TopLearnersColumn({
  learners,
  isLoading,
  error,
  onRetry,
}: {
  learners: TopLearnerItem[];
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
}) {
  if (isLoading) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Top Learners
        </h3>
        <TopLearnersLoadingSkeleton />
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Top Learners
        </h3>
        <div className="text-center py-6">
          <p className="text-red-500 dark:text-red-400 mb-3">
            Failed to load learner data
          </p>
          <button
            onClick={onRetry}
            className="px-4 py-2 text-sm font-medium text-white bg-amber-500 hover:bg-amber-600 rounded-lg transition-colors min-w-[44px] min-h-[44px]"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  if (learners.length === 0) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Top Learners
        </h3>
        <p className="text-gray-500 dark:text-gray-400 text-center py-6">
          No learner activity
        </p>
      </Card>
    );
  }

  return (
    <Card>
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        Top Learners
      </h3>

      {/* Desktop: compact table */}
      <div className="hidden md:block">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
              <th className="pb-2 font-medium">Username</th>
              <th className="pb-2 font-medium">Progress</th>
              <th className="pb-2 font-medium text-right">Modules</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {learners.map((learner) => (
              <tr key={learner.user_id}>
                <td className="py-2 text-gray-900 dark:text-gray-100">
                  {truncate(learner.username, 50)}
                </td>
                <td className="py-2 w-1/3">
                  <div className="flex items-center gap-2">
                    <ProgressBar
                      percentage={learner.percentage}
                      height="sm"
                    />
                    <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                      {learner.percentage}%
                    </span>
                  </div>
                </td>
                <td className="py-2 text-right text-gray-600 dark:text-gray-300">
                  {learner.completed}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile: stacked cards */}
      <div className="md:hidden space-y-3">
        {learners.map((learner) => (
          <div
            key={learner.user_id}
            className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700"
          >
            <p className="font-medium text-gray-900 dark:text-gray-100 text-sm mb-1">
              {truncate(learner.username, 50)}
            </p>
            <div className="flex items-center gap-2 mb-1">
              <ProgressBar percentage={learner.percentage} height="sm" />
              <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                {learner.percentage}%
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {learner.completed} modules completed
            </p>
          </div>
        ))}
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Recent Members Sub-Component
// ---------------------------------------------------------------------------

function RecentMembersColumn({
  isLoading,
  error,
  onRetry,
}: {
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
}) {
  // Recent Members data is not available from the current API.
  // This column renders the structure ready for future data integration.

  if (isLoading) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Recent Members
        </h3>
        <RecentMembersLoadingSkeleton />
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Recent Members
        </h3>
        <div className="text-center py-6">
          <p className="text-red-500 dark:text-red-400 mb-3">
            Failed to load member data
          </p>
          <button
            onClick={onRetry}
            className="px-4 py-2 text-sm font-medium text-white bg-amber-500 hover:bg-amber-600 rounded-lg transition-colors min-w-[44px] min-h-[44px]"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  // Empty state - no recent members API endpoint available
  return (
    <Card>
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        Recent Members
      </h3>
      <p className="text-gray-500 dark:text-gray-400 text-center py-6">
        No recent members
      </p>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// ActivitySection
// ---------------------------------------------------------------------------

export function ActivitySection() {
  const { analytics, isLoading, errors, refetchAll } = useAdminContext();

  // Sort and take top 10 learners
  const topLearners = useMemo(() => {
    if (!analytics?.completion_by_user) return [];
    return sortByCompletionDesc(analytics.completion_by_user).slice(0, 10);
  }, [analytics]);

  const analyticsError = errors.analytics ?? null;

  return (
    <section aria-label="Learner and Member Activity">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <TopLearnersColumn
          learners={topLearners}
          isLoading={isLoading}
          error={analyticsError}
          onRetry={refetchAll}
        />
        <RecentMembersColumn
          isLoading={isLoading}
          error={analyticsError}
          onRetry={refetchAll}
        />
      </div>
    </section>
  );
}
