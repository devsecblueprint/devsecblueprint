'use client';

import { useState, useEffect } from 'react';
import { AuthGuard } from '@/components/AuthGuard';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { apiClient } from '@/lib/api';
import { PathwayCard } from '@/components/certification/PathwayCard';
import type { PathwayWithStatus } from '@/components/certification/PathwayCard';
import type { CandidateStatus } from '@/components/certification/PathwayCard';
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
 * Full-page layout with a stats overview, pathway cards, and
 * certification process info to fill the viewport.
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

  const hasInProgressPathway = pathways.some(
    (p) => p.candidate_status === 'IN_PROGRESS'
  );
  const showFullNameWarning = hasInProgressPathway && !fullName;

  // Stats derived from pathways
  const awarded = pathways.filter((p) => p.candidate_status === 'AWARDED').length;
  const inProgress = pathways.filter((p) => p.candidate_status === 'IN_PROGRESS').length;
  const notStarted = pathways.filter(
    (p) => !p.candidate_status || p.candidate_status === 'NOT_STARTED'
  ).length;

  return (
    <AuthGuard>
      <div className="min-h-screen bg-gray-950">
        <NavbarWithAuth />
        <main className="pt-16 flex flex-col min-h-[calc(100vh-4rem)]">
          <div className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 py-8 sm:py-12 space-y-8 w-full">

            {/* Header row */}
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-100">
                Certifications
              </h1>
              <p className="mt-1 text-sm text-gray-400">
                Track your progress across DSB certification pathways. Earn credentials by completing capstone projects and passing a combined review session.
              </p>
            </div>

            {/* Full name warning banner */}
            {showFullNameWarning && (
              <div className="p-4 bg-yellow-900/20 border border-yellow-800 rounded-xl">
                <div className="flex items-start gap-3">
                  <svg
                    className="w-5 h-5 text-yellow-400 mt-0.5 shrink-0"
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
                    <p className="text-sm font-medium text-yellow-200">
                      Full name required for credential issuance
                    </p>
                    <p className="mt-1 text-sm text-yellow-300">
                      You must set your full legal name before a credential can be issued.{' '}
                      <Link
                        href="/settings/profile"
                        className="font-medium underline hover:text-yellow-100"
                      >
                        Update your profile
                      </Link>
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Stats overview */}
            {!isLoading && !error && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <StatCard label="Total Pathways" value={pathways.length} />
                <StatCard label="Awarded" value={awarded} accent="green" />
                <StatCard label="In Progress" value={inProgress} accent="blue" />
                <StatCard label="Not Started" value={notStarted} accent="gray" />
              </div>
            )}

            {/* Loading state */}
            {isLoading && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="animate-pulse bg-gray-900 border border-gray-800 rounded-xl h-40"
                  />
                ))}
              </div>
            )}

            {/* Error state */}
            {error && !isLoading && (
              <div className="p-4 bg-red-900/20 border border-red-800 rounded-xl">
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            {/* Pathways grid — larger cards */}
            {!isLoading && !error && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {pathways.map((pathway) => (
                  <PathwayCard key={pathway.pathway_id} pathway={pathway} />
                ))}
              </div>
            )}

            {/* Empty state */}
            {!isLoading && !error && pathways.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-400">
                  No certification pathways are available yet.
                </p>
              </div>
            )}

            {/* How it works section — fills remaining space */}
            <div className="mt-auto pt-8 border-t border-gray-800/50">
              <h2 className="text-lg font-semibold text-gray-200 mb-4">
                How Certifications Work
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <StepCard
                  step={1}
                  title="Complete Capstones"
                  description="Finish all required capstone projects within a pathway to become eligible."
                />
                <StepCard
                  step={2}
                  title="Pass Review Session"
                  description="Schedule and pass a combined review session to demonstrate your knowledge."
                />
                <StepCard
                  step={3}
                  title="Earn Your Credential"
                  description="Receive a verifiable credential you can share on LinkedIn and your resume."
                />
              </div>
            </div>
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}

/* ─── Sub-components ──────────────────────────────────────────────────── */

function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent?: 'green' | 'blue' | 'gray';
}) {
  const accentColor = {
    green: 'text-green-400',
    blue: 'text-blue-400',
    gray: 'text-gray-400',
  }[accent ?? 'gray'] ?? 'text-gray-100';

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${accentColor}`}>{value}</p>
    </div>
  );
}

function StepCard({
  step,
  title,
  description,
}: {
  step: number;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-5 flex gap-4">
      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary-400/10 border border-primary-400/30 text-primary-400 text-sm font-bold shrink-0">
        {step}
      </div>
      <div>
        <h3 className="text-sm font-semibold text-gray-200">{title}</h3>
        <p className="mt-1 text-xs text-gray-500 leading-relaxed">{description}</p>
      </div>
    </div>
  );
}
