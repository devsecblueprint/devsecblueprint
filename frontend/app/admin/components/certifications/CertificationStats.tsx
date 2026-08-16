'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { Skeleton } from '@/components/ui/Skeleton';
import { Button } from '@/components/ui/Button';

/**
 * Stats response from GET /admin/certifications/stats
 */
interface CertificationStatsData {
  candidates_by_status: Record<string, number>;
  credentials_by_status: Record<string, number>;
  pending_reviews: number;
}

/**
 * CertificationStats displays a quick stats overview for the admin
 * certification accordion section. Shows summary cards in a responsive
 * 1x3 grid (desktop) for total candidates, credentials issued, and
 * pending reviews.
 *
 * Requirements: 13.1
 */
export function CertificationStats() {
  const [stats, setStats] = useState<CertificationStatsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    const response = await apiClient.get<CertificationStatsData>(
      '/admin/certifications/stats'
    );

    if (response.error) {
      setError(response.error);
      setIsLoading(false);
      return;
    }

    setStats(response.data ?? null);
    setIsLoading(false);
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  if (isLoading) {
    return (
      <div
        className="grid grid-cols-1 sm:grid-cols-3 gap-4"
        aria-busy="true"
        aria-label="Loading certification statistics"
      >
        <StatCardSkeleton />
        <StatCardSkeleton />
        <StatCardSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 dark:border-red-800 p-4 text-center">
        <p className="text-sm text-red-600 dark:text-red-400 mb-3">
          Failed to load certification stats
        </p>
        <Button variant="secondary" size="sm" onClick={fetchStats}>
          Retry
        </Button>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const totalCandidates = Object.values(stats.candidates_by_status).reduce(
    (sum, count) => sum + count,
    0
  );

  const totalCredentials = Object.values(stats.credentials_by_status).reduce(
    (sum, count) => sum + count,
    0
  );

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <StatCard
        value={totalCandidates}
        label="Total Candidates"
        breakdown={stats.candidates_by_status}
      />
      <StatCard
        value={totalCredentials}
        label="Credentials Issued"
        breakdown={stats.credentials_by_status}
      />
      <StatCard
        value={stats.pending_reviews}
        label="Pending Reviews"
      />
    </div>
  );
}

/**
 * Individual stat card with a number, label, and optional status breakdown.
 */
function StatCard({
  value,
  label,
  breakdown,
}: {
  value: number;
  label: string;
  breakdown?: Record<string, number>;
}) {
  return (
    <div className="rounded-lg bg-gray-50 dark:bg-gray-800 p-4">
      <p className="text-2xl font-bold text-amber-500 dark:text-amber-400">
        {value}
      </p>
      <p className="text-sm text-gray-700 dark:text-gray-300">{label}</p>
      {breakdown && Object.keys(breakdown).length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2">
          {Object.entries(breakdown).map(([status, count]) => (
            <span
              key={status}
              className="inline-flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400"
            >
              <span className="font-medium">{count}</span>
              <span>{formatStatus(status)}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Skeleton placeholder for a stat card during loading.
 */
function StatCardSkeleton() {
  return (
    <div className="rounded-lg bg-gray-50 dark:bg-gray-800 p-4">
      <Skeleton className="h-8 w-16 mb-2" />
      <Skeleton className="h-4 w-28 mb-2" />
      <Skeleton className="h-3 w-36" />
    </div>
  );
}

/**
 * Format a status enum value for display (e.g., "IN_PROGRESS" → "In Progress").
 */
function formatStatus(status: string): string {
  return status
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
