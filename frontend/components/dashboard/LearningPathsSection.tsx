'use client';

import Link from 'next/link';
import { getAllCourses, CourseProgress } from '@/lib/course-utils';
import { LearningPathCard } from '@/components/dashboard/LearningPathCard';

export interface LearningPathsSectionProps {
  progress: Record<string, boolean>;
  isLoading: boolean;
}

/**
 * LearningPathsSection displays up to 3 learning paths with progress,
 * sorted by most recent activity (highest completedPages first as a proxy).
 * Shows empty state when no paths have progress, and a "View All" link
 * when more than 3 paths have progress.
 */
export function LearningPathsSection({ progress, isLoading }: LearningPathsSectionProps) {
  // Loading state: show 3 skeleton cards
  if (isLoading) {
    return (
      <section>
        <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
          My Learning Paths
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="bg-white dark:bg-gray-900 rounded-2xl shadow-lg p-6 animate-pulse"
            >
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="h-5 w-32 bg-gray-200 dark:bg-gray-800 rounded" />
                <div className="h-4 w-10 bg-gray-200 dark:bg-gray-800 rounded" />
              </div>
              <div className="h-2 w-full bg-gray-200 dark:bg-gray-800 rounded-full mb-3" />
              <div className="h-4 w-40 bg-gray-200 dark:bg-gray-800 rounded mb-2" />
              <div className="h-4 w-48 bg-gray-200 dark:bg-gray-800 rounded mb-4" />
              <div className="h-9 w-24 bg-gray-200 dark:bg-gray-800 rounded-lg" />
            </div>
          ))}
        </div>
      </section>
    );
  }

  // Compute course progress from raw progress data
  const allCourses = getAllCourses(progress);

  // Filter to paths that have at least 1 completed page (i.e., have progress)
  // Exclude walkthroughs as the existing dashboard does
  const pathsWithProgress = allCourses.filter(
    (course) => course.learningPath !== 'Walkthroughs' && course.completedPages > 0
  );

  // Sort by most recently progressed (highest completedPages as proxy for recent activity)
  const sortedPaths = [...pathsWithProgress].sort(
    (a, b) => b.completedPages - a.completedPages
  );

  // Show empty state when no paths have progress
  if (sortedPaths.length === 0) {
    return (
      <section>
        <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
          My Learning Paths
        </h2>
        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-lg p-6 text-center">
          <div className="mb-4">
            <svg
              className="w-12 h-12 mx-auto text-gray-400 dark:text-gray-600"
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
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            You haven't started any learning paths yet.
          </p>
          <Link
            href="/courses"
            className="inline-flex items-center justify-center px-5 py-2.5 text-sm font-semibold text-gray-900 bg-amber-500 dark:bg-amber-400 rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
          >
            Browse Courses
            <svg
              className="w-4 h-4 ml-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M14 5l7 7m0 0l-7 7m7-7H3"
              />
            </svg>
          </Link>
        </div>
      </section>
    );
  }

  // Show max 3 paths
  const displayedPaths = sortedPaths.slice(0, 3);
  const hasMorePaths = sortedPaths.length > 3;

  return (
    <section>
      <div className="flex items-center justify-between mb-4 sm:mb-6">
        <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-gray-100">
          My Learning Paths
        </h2>
        {hasMorePaths && (
          <Link
            href="/courses"
            className="inline-flex items-center text-sm font-medium text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 rounded"
          >
            View All
            <svg
              className="w-4 h-4 ml-1"
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
          </Link>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {displayedPaths.map((course) => (
          <LearningPathCard
            key={`${course.learningPath}-${course.topic}`}
            title={course.title}
            percentComplete={course.percentComplete}
            completedPages={course.completedPages}
            totalPages={course.totalPages}
            actionHref={
              course.percentComplete === 100
                ? course.firstPageSlug
                : course.lastActiveSlug
            }
            actionLabel={course.percentComplete === 100 ? 'View' : 'Continue'}
          />
        ))}
      </div>
    </section>
  );
}
