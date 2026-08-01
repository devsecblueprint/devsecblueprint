'use client';

import Link from 'next/link';
import { Card } from '@/components/ui/Card';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { getAllCourses, CourseProgress } from '@/lib/course-utils';

export interface ContinueLearningCardProps {
  progress: Record<string, boolean>;
  progressLoading: boolean;
  lastActiveSlug: string | null;
  lastActiveLessonLoading: boolean;
}

/**
 * ContinueLearningCard displays one of three mutually exclusive states:
 * 1. Onboarding (new user): no progress or all at 0%
 * 2. Active learning: at least one course between 1-99%
 * 3. Completion: all courses at 100%
 *
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 8.7
 */
export function ContinueLearningCard({
  progress,
  progressLoading,
  lastActiveSlug,
  lastActiveLessonLoading,
}: ContinueLearningCardProps) {
  // Skeleton loading state
  if (progressLoading) {
    return (
      <section className="w-full">
        <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
          Continue Where You Left Off
        </h2>
        <Card padding="lg">
          <div className="animate-pulse space-y-4 py-4">
            <div className="h-5 w-24 bg-gray-200 dark:bg-gray-800 rounded" />
            <div className="h-7 w-64 bg-gray-200 dark:bg-gray-800 rounded" />
            <div className="h-4 w-48 bg-gray-200 dark:bg-gray-800 rounded" />
            <div className="h-3 w-full max-w-xs bg-gray-200 dark:bg-gray-800 rounded-full" />
            <div className="flex gap-3 pt-2">
              <div className="h-11 w-40 bg-gray-200 dark:bg-gray-800 rounded-lg" />
              <div className="h-11 w-28 bg-gray-200 dark:bg-gray-800 rounded-lg" />
            </div>
          </div>
        </Card>
      </section>
    );
  }

  // Compute course data from progress
  const allCourses = getAllCourses(progress, lastActiveSlug ?? undefined);

  // Filter out walkthroughs
  const courses = allCourses.filter(
    (course) => course.learningPath !== 'Walkthroughs'
  );

  // Determine state
  const incompleteCourses = courses.filter(
    (course) => course.percentComplete > 0 && course.percentComplete < 100
  );
  const completedCourses = courses.filter(
    (course) => course.percentComplete === 100
  );
  const hasAnyProgress = courses.some((course) => course.percentComplete > 0);
  const allComplete =
    courses.length > 0 && completedCourses.length === courses.length;

  // Determine which state to show
  const isNewUser = !hasAnyProgress;
  const isComplete = allComplete;
  const isActiveLearning = !isNewUser && !isComplete;

  // Find resume course for active learning state
  let resumeCourse: CourseProgress | undefined;
  if (isActiveLearning) {
    if (lastActiveSlug) {
      resumeCourse = incompleteCourses.find(
        (course) => course.lastActiveSlug === lastActiveSlug
      );
    }
    if (!resumeCourse && incompleteCourses.length > 0) {
      resumeCourse = incompleteCourses[0];
    }
    // If no incomplete courses found but user has progress (edge case: some at 0%, some at 100%)
    if (!resumeCourse) {
      const zeroCourses = courses.filter((c) => c.percentComplete === 0);
      if (zeroCourses.length > 0) {
        resumeCourse = zeroCourses[0];
      }
    }
  }

  // Determine section heading
  const heading = isNewUser
    ? 'Start Your Learning Journey'
    : isComplete
      ? 'Congratulations!'
      : 'Continue Where You Left Off';

  return (
    <section className="w-full">
      <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
        {heading}
      </h2>
      <Card padding="lg">
        {isNewUser && <OnboardingState />}
        {isComplete && <CompletionState />}
        {isActiveLearning && (
          <ActiveLearningState
            course={resumeCourse!}
            lastActiveLessonLoading={lastActiveLessonLoading}
          />
        )}
      </Card>
    </section>
  );
}

/** Onboarding state for new users with no progress */
function OnboardingState() {
  return (
    <div className="text-center py-8">
      <div className="mb-6">
        <svg
          className="w-16 h-16 mx-auto text-amber-500 dark:text-amber-400"
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
      <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-3">
        Welcome to The DevSec Blueprint!
      </h3>
      <p className="text-base text-gray-600 dark:text-gray-400 mb-6 max-w-2xl mx-auto">
        You&apos;re all set to begin your journey into DevSecOps and Cloud Security
        Development. Start with any learning path below, and your progress will be
        tracked automatically.
      </p>
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <Link
          href="/courses"
          className="inline-flex items-center justify-center px-6 py-3 bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
        >
          <span>Browse All Courses</span>
          <svg
            className="w-5 h-5 ml-2"
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
        <Link
          href="/learn/welcome"
          className="inline-flex items-center justify-center px-6 py-3 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 font-semibold rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
        >
          Read Welcome Message
        </Link>
      </div>
    </div>
  );
}

/** Completion state when all courses are at 100% */
function CompletionState() {
  return (
    <div className="text-center py-8">
      <div className="mb-6">
        <svg
          className="w-20 h-20 mx-auto text-green-500 dark:text-green-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>
      <h3 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-3">
        You&apos;ve Completed All Available Courses!
      </h3>
      <p className="text-lg text-gray-600 dark:text-gray-400 mb-6 max-w-2xl mx-auto">
        Amazing work! You&apos;ve mastered all the current content. Check back soon
        for new courses, or review what you&apos;ve learned to reinforce your
        knowledge.
      </p>
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <Link
          href="/courses"
          className="inline-flex items-center justify-center px-6 py-3 bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
        >
          <span>Review Courses</span>
          <svg
            className="w-5 h-5 ml-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        </Link>
      </div>
    </div>
  );
}

/** Active learning state showing current course progress */
function ActiveLearningState({
  course,
  lastActiveLessonLoading,
}: {
  course: CourseProgress;
  lastActiveLessonLoading: boolean;
}) {
  const continueHref = course.lastActiveSlug;

  return (
    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
      <div className="flex-1">
        <h3 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          {course.title}
        </h3>
        <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 mb-4">
          {course.completedPages} of {course.totalPages} pages completed
        </p>
        <div className="flex items-center space-x-4">
          <div className="flex-1 max-w-xs">
            <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
              <span>Progress</span>
              <span>{course.percentComplete}%</span>
            </div>
            <ProgressBar
              percentage={course.percentComplete}
              height="sm"
            />
          </div>
          <span className="text-xs text-gray-600 dark:text-gray-400 whitespace-nowrap">
            {course.completedPages}/{course.totalPages} pages
          </span>
        </div>
      </div>
      <div className="flex flex-col sm:flex-row gap-3">
        {lastActiveLessonLoading ? (
          <button
            disabled
            aria-disabled="true"
            className="inline-flex items-center justify-center px-6 py-3 bg-amber-300 dark:bg-amber-600 text-gray-700 dark:text-gray-300 font-semibold rounded-lg cursor-not-allowed"
          >
            <svg
              className="animate-spin w-5 h-5 mr-2"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            <span>Loading...</span>
          </button>
        ) : (
          <Link
            href={continueHref}
            className="inline-flex items-center justify-center px-6 py-3 bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
          >
            <span>Continue Learning</span>
            <svg
              className="w-5 h-5 ml-2"
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
        )}
        <Link
          href="/courses"
          className="inline-flex items-center justify-center px-6 py-3 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 font-semibold rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
        >
          View Path
        </Link>
      </div>
    </div>
  );
}
