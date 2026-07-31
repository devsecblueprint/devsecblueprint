'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { useAdminContext } from './AdminDashboardProvider';
import { KpiCard } from './KpiCard';

/**
 * PlatformSummary renders the top-level KPI grid for the Admin Dashboard.
 *
 * - Consumes `kpiMetrics`, `isLoading`, `errors`, and `refetchAll` from context
 * - Displays a responsive grid: 6-col on xl (≥1280px), 3-col on md (≥768px), 2-col below
 * - Shows loading skeletons while data is fetching
 * - Shows an inline error with retry when analytics fails
 * - Builder Members card auto-hides when unavailable (the metrics array is pre-filtered)
 */
export function PlatformSummary() {
  const { kpiMetrics, isLoading, errors, refetchAll } = useAdminContext();

  const hasAnalyticsError = Boolean(errors.analytics);

  return (
    <Card className="mb-6">
      {/* Section header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Platform Analytics
        </h2>
        <button
          onClick={refetchAll}
          disabled={isLoading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Refresh platform analytics"
        >
          <svg
            className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Refresh
        </button>
      </div>

      {/* Error state */}
      {hasAnalyticsError && !isLoading && (
        <div
          className="flex items-center justify-between rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-4 mb-4"
          role="alert"
        >
          <p className="text-sm text-red-700 dark:text-red-300">
            Failed to load analytics data.
          </p>
          <button
            onClick={refetchAll}
            className="ml-4 px-3 py-1.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        {isLoading
          ? /* Render 6 skeleton cards while loading */
            Array.from({ length: 6 }).map((_, index) => (
              <KpiCard
                key={`skeleton-${index}`}
                label=""
                value=""
                isLoading
              />
            ))
          : /* Render actual KPI metrics (pre-filtered for visibility by the provider) */
            kpiMetrics.map((metric) => (
              <KpiCard
                key={metric.id}
                label={metric.label}
                value={metric.value}
                sublabel={metric.sublabel}
                onClick={metric.onClick}
              />
            ))}
      </div>
    </Card>
  );
}
