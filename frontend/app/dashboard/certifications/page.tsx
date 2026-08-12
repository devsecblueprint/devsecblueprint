'use client';

import { useState, useEffect } from 'react';
import { AuthGuard } from '@/components/AuthGuard';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { apiClient } from '@/lib/api';
import { PathwayCard } from '@/components/certification/PathwayCard';
import type { PathwayWithStatus } from '@/components/certification/PathwayCard';
import Link from 'next/link';

/**
 * User profile shape (subset needed for full_name check)
 */
interface UserProfile {
  full_name?: string | null;
}

/**
 * Certifications dashboard page.
 *
 * Displays all available certification pathways with the learner's
 * current CandidateStatus for each, including the auto-calculated
 * Completionist pathway. Shows a warning banner if any pathway is
 * IN_PROGRESS and the learner has not set their full_name.
 *
 * Route: /dashboard/certifications
 * Requirements: 12.1, 12.2, 12.5, 3.8
 */
export default function CertificationsDashboardPage() {
  const [pathways, setPathways] = useState<PathwayWithStatus[]>([]);
  const [fullName, setFullName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Fetch pathways with status and user profile in parallel
        const [pathwaysRes, profileRes] = await Promise.all([
          apiClient.get<PathwayWithStatus[]>('/certifications'),
          apiClient.get<UserProfile>('/user/profile'),
        ]);

        if (pathwaysRes.error) {
          setError(pathwaysRes.error);
          return;
        }

        if (pathwaysRes.data) {
          setPathways(pathwaysRes.data);
        }

        if (profileRes.data) {
          setFullName(profileRes.data.full_name || null);
        }
      } catch (err) {
        setError('Failed to load certification data. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // Determine if we should show the full_name warning banner
  const hasInProgressPathway = pathways.some(
    (p) => p.candidate_status === 'IN_PROGRESS'
  );
  const showFullNameWarning = hasInProgressPathway && !fullName;

  return (
    <AuthGuard>
      <div className="min-h-screen bg-white dark:bg-gray-950">
        <NavbarWithAuth />
        <main className="pt-16">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
            {/* Page header */}
            <div className="mb-8">
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100">
                Certifications
              </h1>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Track your progress across DSB certification pathways. Earn credentials by completing capstone projects and passing a combined review session.
              </p>
            </div>

            {/* Full name warning banner */}
            {showFullNameWarning && (
              <div className="mb-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                <div className="flex items-start gap-3">
                  <svg
                    className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5 shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                    />
                  </svg>
                  <div>
                    <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                      Full name required for credential issuance
                    </p>
                    <p className="mt-1 text-sm text-yellow-700 dark:text-yellow-300">
                      You must set your full legal name before a credential can be issued.{' '}
                      <Link
                        href="/settings/profile"
                        className="font-medium underline hover:text-yellow-900 dark:hover:text-yellow-100"
                      >
                        Update your profile
                      </Link>
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Loading state */}
            {isLoading && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="animate-pulse bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="h-5 bg-gray-200 dark:bg-gray-800 rounded w-48 mb-3" />
                        <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-full mb-2" />
                        <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-2/3" />
                      </div>
                      <div className="h-5 bg-gray-200 dark:bg-gray-800 rounded w-20" />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Error state */}
            {error && !isLoading && (
              <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
              </div>
            )}

            {/* Pathways grid */}
            {!isLoading && !error && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {pathways.map((pathway) => (
                  <PathwayCard key={pathway.pathway_id} pathway={pathway} />
                ))}
              </div>
            )}

            {/* Empty state */}
            {!isLoading && !error && pathways.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-500 dark:text-gray-400">
                  No certification pathways are available yet.
                </p>
              </div>
            )}
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
