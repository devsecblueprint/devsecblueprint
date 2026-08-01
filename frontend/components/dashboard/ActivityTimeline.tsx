'use client';

import { useRecentActivities } from '@/lib/hooks/useRecentActivities';
import { Card } from '@/components/ui/Card';
import { SkeletonActivityCard } from '@/components/ui/Skeleton';

/**
 * ActivityTimeline Component
 *
 * Displays up to 5 recent activities ordered by most recent first.
 * Each activity shows an icon based on type, a title, and a relative timestamp.
 *
 * Calls useRecentActivities() internally. Shows skeleton while loading,
 * empty state on error or no activities.
 *
 * Requirements: 5.1, 5.2, 5.3, 5.4, 5.9, 5.11
 */

const MAX_VISIBLE_ACTIVITIES = 5;

/**
 * Determine activity type from title or path keywords.
 */
function getActivityType(title: string, path: string): 'quiz' | 'walkthrough' | 'badge' | 'lesson' {
  const combined = `${title} ${path}`.toLowerCase();
  if (combined.includes('quiz')) return 'quiz';
  if (combined.includes('walkthrough')) return 'walkthrough';
  if (combined.includes('badge')) return 'badge';
  return 'lesson';
}

/**
 * Icon for quiz passed (checkmark in green circle)
 */
function QuizIcon() {
  return (
    <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 border border-green-300 dark:border-green-700 flex items-center justify-center flex-shrink-0">
      <svg
        className="w-5 h-5 text-green-600 dark:text-green-400"
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
    </div>
  );
}

/**
 * Icon for lesson completed (book in green circle)
 */
function LessonIcon() {
  return (
    <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 border border-green-300 dark:border-green-700 flex items-center justify-center flex-shrink-0">
      <svg
        className="w-5 h-5 text-green-600 dark:text-green-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
        />
      </svg>
    </div>
  );
}

/**
 * Icon for walkthrough started (code brackets in amber circle)
 */
function WalkthroughIcon() {
  return (
    <div className="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/30 border border-amber-300 dark:border-amber-700 flex items-center justify-center flex-shrink-0">
      <svg
        className="w-5 h-5 text-amber-600 dark:text-amber-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
        />
      </svg>
    </div>
  );
}

/**
 * Icon for badge earned (trophy in purple circle)
 */
function BadgeIcon() {
  return (
    <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 border border-purple-300 dark:border-purple-700 flex items-center justify-center flex-shrink-0">
      <svg
        className="w-5 h-5 text-purple-600 dark:text-purple-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
        />
      </svg>
    </div>
  );
}

/**
 * Return the appropriate icon component for an activity type.
 */
function ActivityIcon({ type }: { type: 'quiz' | 'walkthrough' | 'badge' | 'lesson' }) {
  switch (type) {
    case 'quiz':
      return <QuizIcon />;
    case 'walkthrough':
      return <WalkthroughIcon />;
    case 'badge':
      return <BadgeIcon />;
    case 'lesson':
    default:
      return <LessonIcon />;
  }
}

export function ActivityTimeline() {
  const { activities, isLoading, error } = useRecentActivities();

  // Sort by most recent first and take at most 5
  const sortedActivities = [...activities]
    .sort((a, b) => new Date(b.completedAt).getTime() - new Date(a.completedAt).getTime())
    .slice(0, MAX_VISIBLE_ACTIVITIES);

  return (
    <section aria-labelledby="recent-activity-heading">
      <h2
        id="recent-activity-heading"
        className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6"
      >
        Recent Activity
      </h2>

      {isLoading ? (
        <div className="space-y-3" aria-live="polite" aria-busy="true">
          {Array.from({ length: 5 }).map((_, i) => (
            <SkeletonActivityCard key={i} />
          ))}
        </div>
      ) : error || sortedActivities.length === 0 ? (
        <Card padding="md">
          <div className="text-center py-8">
            <svg
              className="w-12 h-12 mx-auto text-gray-400 dark:text-gray-600 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              No recent activity yet. Start a lesson or quiz to see your progress here!
            </p>
            <a
              href="/courses"
              className="inline-block mt-4 text-sm font-medium text-amber-500 dark:text-amber-400 hover:underline focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 rounded"
            >
              Browse Courses
            </a>
          </div>
        </Card>
      ) : (
        <div className="space-y-3" aria-live="polite" aria-busy="false">
          {sortedActivities.map((activity) => {
            const type = getActivityType(activity.title, activity.path);
            return (
              <Card key={activity.id} padding="md">
                <div className="flex items-center space-x-4">
                  <ActivityIcon type={type} />
                  <div className="flex-1 min-w-0">
                    <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 truncate">
                      {activity.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {activity.path}
                    </p>
                  </div>
                  <div className="flex-shrink-0">
                    <span className="text-xs text-gray-500 dark:text-gray-500">
                      {activity.relativeTime}
                    </span>
                  </div>
                </div>
              </Card>
            );
          })}

        </div>
      )}
    </section>
  );
}
