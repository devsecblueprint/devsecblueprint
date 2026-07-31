'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Spinner } from '@/components/ui/Spinner';
import { useAdminContext } from './AdminDashboardProvider';
import { validateDateRange } from './utils';
import type { DateRange } from './types';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Returns an ISO date string (YYYY-MM-DD) offset by `days` from today. */
function getDateOffset(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0];
}

/** Determines whether the current viewport width is below 576px. */
function useIsMobile(): boolean {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia('(max-width: 575px)');
    setIsMobile(mql.matches);
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, []);

  return isMobile;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const TIMEOUT_MS = 10_000;

export function RegistrationAnalytics() {
  const { analytics, isLoading, errors, refetchAnalytics } = useAdminContext();
  const isMobile = useIsMobile();

  // Date range state — defaults to last 30 days
  const [dateRange, setDateRange] = useState<DateRange>({
    startDate: getDateOffset(-30),
    endDate: getDateOffset(0),
  });
  const [dateError, setDateError] = useState<string | null>(null);

  // Timeout state
  const [timedOut, setTimedOut] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Start/clear timeout when loading state changes
  useEffect(() => {
    if (isLoading) {
      timerRef.current = setTimeout(() => setTimedOut(true), TIMEOUT_MS);
    } else {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      setTimedOut(false);
    }
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [isLoading]);

  // ---------------------------------------------------------------------------
  // Date range handler
  // ---------------------------------------------------------------------------

  const handleDateChange = useCallback(
    (field: 'startDate' | 'endDate', value: string) => {
      const updated: DateRange = { ...dateRange, [field]: value };
      setDateRange(updated);

      const result = validateDateRange(updated);
      setDateError(result.valid ? null : result.error ?? 'Invalid range');
    },
    [dateRange]
  );

  // ---------------------------------------------------------------------------
  // Filtered timeline data
  // ---------------------------------------------------------------------------

  const filteredTimeline = useMemo(() => {
    if (!analytics?.registration_timeline) return [];
    const start = new Date(dateRange.startDate).getTime();
    const end = new Date(dateRange.endDate).getTime();
    if (isNaN(start) || isNaN(end)) return analytics.registration_timeline;

    return analytics.registration_timeline.filter((d) => {
      const t = new Date(d.date).getTime();
      return t >= start && t <= end;
    });
  }, [analytics, dateRange]);

  // ---------------------------------------------------------------------------
  // Retry handler
  // ---------------------------------------------------------------------------

  const handleRetry = useCallback(() => {
    setTimedOut(false);
    refetchAnalytics();
  }, [refetchAnalytics]);

  // ---------------------------------------------------------------------------
  // Render states
  // ---------------------------------------------------------------------------

  // Error from context (API failure) or timeout
  const hasError = !!errors.analytics || timedOut;

  return (
    <Card padding="lg" className="w-full">
      {/* Header + date controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          New User Registrations
        </h3>

        <div className="flex flex-col xs:flex-row items-start xs:items-center gap-2">
          <label className="sr-only" htmlFor="reg-start-date">
            Start date
          </label>
          <input
            id="reg-start-date"
            type="date"
            value={dateRange.startDate}
            onChange={(e) => handleDateChange('startDate', e.target.value)}
            className="rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-2 py-1 text-sm text-gray-900 dark:text-gray-100"
            aria-label="Start date"
          />
          <span className="text-gray-500 dark:text-gray-400 text-sm">to</span>
          <label className="sr-only" htmlFor="reg-end-date">
            End date
          </label>
          <input
            id="reg-end-date"
            type="date"
            value={dateRange.endDate}
            onChange={(e) => handleDateChange('endDate', e.target.value)}
            className="rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-2 py-1 text-sm text-gray-900 dark:text-gray-100"
            aria-label="End date"
          />
        </div>
      </div>

      {dateError && (
        <p className="text-sm text-red-600 dark:text-red-400 mb-4" role="alert">
          {dateError}
        </p>
      )}

      {/* Chart area */}
      <div className="relative min-h-[300px]">
        {/* Loading state */}
        {isLoading && !timedOut && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/60 dark:bg-gray-900/60 rounded-lg z-10">
            <Spinner size="lg" />
          </div>
        )}

        {/* Error / timeout state */}
        {hasError && !isLoading ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <p className="text-sm text-red-600 dark:text-red-400 mb-4">
              {timedOut
                ? 'Loading timed out. Please try again.'
                : errors.analytics ?? 'Failed to load registration data.'}
            </p>
            <button
              onClick={handleRetry}
              className="px-4 py-2 text-sm font-medium rounded-md bg-amber-500 text-white hover:bg-amber-600 transition-colors"
            >
              Retry
            </button>
          </div>
        ) : timedOut && isLoading ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <p className="text-sm text-red-600 dark:text-red-400 mb-4">
              Loading timed out. Please try again.
            </p>
            <button
              onClick={handleRetry}
              className="px-4 py-2 text-sm font-medium rounded-md bg-amber-500 text-white hover:bg-amber-600 transition-colors"
            >
              Retry
            </button>
          </div>
        ) : !isLoading && filteredTimeline.length === 0 ? (
          /* Empty state */
          <div className="flex items-center justify-center py-16 text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              No registration data available for the selected date range
            </p>
          </div>
        ) : !isLoading && filteredTimeline.length > 0 ? (
          /* Chart */
          <div className="relative">
            {/* Y-axis label */}
            <span
              className="absolute left-0 top-1/2 -translate-y-1/2 -rotate-90 origin-center text-xs text-gray-500 dark:text-gray-400"
              style={{ fontSize: '12px' }}
              aria-hidden="true"
            >
              Count
            </span>

            <svg
              viewBox="0 0 800 300"
              className="w-full h-64"
              preserveAspectRatio="xMidYMid meet"
              role="img"
              aria-label="Line chart showing new user registrations over time"
            >
              {/* Grid lines */}
              <line x1="50" y1="250" x2="750" y2="250" stroke="currentColor" strokeWidth="1" className="text-gray-300 dark:text-gray-700" />
              <line x1="50" y1="200" x2="750" y2="200" stroke="currentColor" strokeWidth="1" className="text-gray-300 dark:text-gray-700" strokeDasharray="4" />
              <line x1="50" y1="150" x2="750" y2="150" stroke="currentColor" strokeWidth="1" className="text-gray-300 dark:text-gray-700" strokeDasharray="4" />
              <line x1="50" y1="100" x2="750" y2="100" stroke="currentColor" strokeWidth="1" className="text-gray-300 dark:text-gray-700" strokeDasharray="4" />
              <line x1="50" y1="50" x2="750" y2="50" stroke="currentColor" strokeWidth="1" className="text-gray-300 dark:text-gray-700" strokeDasharray="4" />

              {/* Y-axis */}
              <line x1="50" y1="30" x2="50" y2="250" stroke="currentColor" strokeWidth="2" className="text-gray-400 dark:text-gray-600" />

              {/* X-axis */}
              <line x1="50" y1="250" x2="750" y2="250" stroke="currentColor" strokeWidth="2" className="text-gray-400 dark:text-gray-600" />

              {/* Y-axis labels */}
              {(() => {
                const maxCount = Math.max(...filteredTimeline.map((d) => d.count), 1);
                const step = Math.ceil(maxCount / 4);
                return [0, 1, 2, 3, 4].map((i) => {
                  const value = i * step;
                  const y = 250 - i * 50;
                  return (
                    <text
                      key={i}
                      x="40"
                      y={y + 5}
                      textAnchor="end"
                      className="fill-gray-600 dark:fill-gray-400"
                      style={{ fontSize: '12px' }}
                    >
                      {value}
                    </text>
                  );
                });
              })()}

              {/* Line path + data points */}
              {(() => {
                const maxCount = Math.max(...filteredTimeline.map((d) => d.count), 1);
                const points = filteredTimeline.map((d, i) => {
                  const x = filteredTimeline.length === 1
                    ? 400
                    : 50 + i * (700 / (filteredTimeline.length - 1));
                  const y = 250 - (d.count / maxCount) * 200;
                  return `${x},${y}`;
                }).join(' ');

                return (
                  <>
                    <polyline
                      points={points}
                      fill="none"
                      stroke="rgb(245, 158, 11)"
                      strokeWidth="3"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    {filteredTimeline.map((d, i) => {
                      const x = filteredTimeline.length === 1
                        ? 400
                        : 50 + i * (700 / (filteredTimeline.length - 1));
                      const y = 250 - (d.count / maxCount) * 200;
                      return (
                        <g key={i}>
                          <circle
                            cx={x}
                            cy={y}
                            r="4"
                            fill="rgb(245, 158, 11)"
                          />
                          {d.count > 0 && (
                            <title>{`${d.date}: ${d.count} registration${d.count !== 1 ? 's' : ''}`}</title>
                          )}
                        </g>
                      );
                    })}
                  </>
                );
              })()}

              {/* X-axis labels — mobile shows max 4 */}
              {(() => {
                const len = filteredTimeline.length;
                if (len === 0) return null;

                // Determine which indices get labels
                let labelIndices: number[];
                if (isMobile) {
                  // Spread max 4 labels evenly
                  const maxLabels = Math.min(4, len);
                  labelIndices = Array.from({ length: maxLabels }, (_, i) =>
                    maxLabels === 1 ? 0 : Math.round(i * (len - 1) / (maxLabels - 1))
                  );
                } else {
                  // Show every 5th day + last
                  labelIndices = filteredTimeline
                    .map((_, i) => i)
                    .filter((i) => i % 5 === 0 || i === len - 1);
                }

                return labelIndices.map((i) => {
                  const x = len === 1
                    ? 400
                    : 50 + i * (700 / (len - 1));
                  const dateObj = new Date(filteredTimeline[i].date);
                  const label = `${dateObj.getMonth() + 1}/${dateObj.getDate()}`;
                  return (
                    <text
                      key={i}
                      x={x}
                      y="270"
                      textAnchor="middle"
                      className="fill-gray-600 dark:fill-gray-400"
                      style={{ fontSize: '12px' }}
                    >
                      {label}
                    </text>
                  );
                });
              })()}
            </svg>

            {/* X-axis label */}
            <p
              className="text-center text-xs text-gray-500 dark:text-gray-400 mt-1"
              style={{ fontSize: '12px' }}
              aria-hidden="true"
            >
              Date
            </p>

            {/* Legend */}
            <div className="mt-4 text-center">
              <span className="inline-flex items-center text-sm text-gray-600 dark:text-gray-400">
                <span className="w-3 h-3 bg-amber-500 rounded-full mr-2" aria-hidden="true" />
                New Registrations
              </span>
            </div>
          </div>
        ) : null}
      </div>
    </Card>
  );
}
