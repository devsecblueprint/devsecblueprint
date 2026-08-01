'use client';

import Link from 'next/link';
import type { ContributorRole } from '@/lib/types';

interface DashboardHeaderProps {
  username: string | null;
  isAdmin: boolean;
  contributorRole: ContributorRole | null;
  isLoading: boolean;
}

/**
 * Truncates a username to a maximum of 50 characters.
 */
function truncateUsername(username: string): string {
  if (username.length <= 50) return username;
  return username.slice(0, 50);
}

export function DashboardHeader({
  username,
  isAdmin,
  contributorRole,
  isLoading,
}: DashboardHeaderProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-3">
          <div
            className="h-9 w-64 bg-gray-200 dark:bg-gray-800 rounded animate-pulse"
            aria-hidden="true"
          />
          <div
            className="h-5 w-96 max-w-full bg-gray-200 dark:bg-gray-800 rounded animate-pulse"
            aria-hidden="true"
          />
        </div>
        <div
          className="h-10 w-36 bg-gray-200 dark:bg-gray-800 rounded animate-pulse"
          aria-hidden="true"
        />
      </div>
    );
  }

  const displayName =
    username && username.trim().length > 0
      ? truncateUsername(username.trim())
      : null;

  const welcomeMessage = displayName
    ? `Welcome back, ${displayName}`
    : 'Welcome back';

  return (
    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
      <div className="min-w-0">
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100">
            {welcomeMessage}
          </h1>

          {contributorRole && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400">
              <svg
                className="w-3.5 h-3.5 mr-1.5"
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
              Contributor
            </span>
          )}

          {isAdmin && (
            <Link
              href="/admin"
              className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
            >
              <svg
                className="w-3.5 h-3.5 mr-1.5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                />
              </svg>
              Admin
            </Link>
          )}
        </div>

        <p className="mt-2 text-sm sm:text-base text-gray-600 dark:text-gray-400">
          Continue building your DevSecOps and Cloud Security skills.
        </p>
      </div>

      <Link
        href="/courses"
        className="inline-flex items-center justify-center px-4 py-2 text-sm font-semibold text-gray-900 bg-amber-500 dark:bg-amber-400 rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950 whitespace-nowrap self-start"
      >
        View All Courses
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
  );
}
