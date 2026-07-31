/**
 * Pure utility functions for the Admin Dashboard.
 *
 * Every function in this module is pure (no side effects) and operates
 * exclusively on its inputs. This makes them straightforward to unit-test
 * and property-test.
 */

import type {
  AnalyticsData,
  AttentionCounts,
  DateRange,
  KpiMetric,
} from './types';
import type {
  CapstoneSubmissionsResponse,
  ModuleHealthResponse,
  RegistryStatusResponse,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// Date range validation
// ---------------------------------------------------------------------------

/**
 * Validates a date range ensuring both dates are valid, start <= end, and the
 * span is between 1 and 365 days inclusive.
 */
export function validateDateRange(range: DateRange): { valid: boolean; error?: string } {
  const start = new Date(range.startDate);
  const end = new Date(range.endDate);

  if (isNaN(start.getTime()) || isNaN(end.getTime())) {
    return { valid: false, error: 'Invalid date format' };
  }
  if (start > end) {
    return { valid: false, error: 'Start date must be before end date' };
  }
  const diffDays = Math.ceil(
    (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)
  );
  if (diffDays < 1) {
    return { valid: false, error: 'Minimum range is 1 day' };
  }
  if (diffDays > 365) {
    return { valid: false, error: 'Maximum range is 365 days' };
  }
  return { valid: true };
}

// ---------------------------------------------------------------------------
// KPI metrics builder
// ---------------------------------------------------------------------------

/**
 * Builds the array of visible KPI metrics from analytics data.
 * Metrics with `visible: false` are filtered out (e.g. Builder Members when
 * `users_completed_all` is 0).
 */
export function buildKpiMetrics(
  analytics: AnalyticsData | null,
  activeSessionsCount: number | null,
  openSessionsModal: () => void
): KpiMetric[] {
  if (!analytics) return [];

  const metrics: KpiMetric[] = [
    {
      id: 'total-users',
      label: 'Total Registered Users',
      value: analytics.total_registered_users,
      sublabel: 'All-time sign-ups',
      visible: true,
    },
    {
      id: 'active-learners',
      label: 'Active Learners (7-day)',
      value: analytics.active_learners_7d,
      sublabel: 'Last 7 days',
      visible: true,
    },
    {
      id: 'builder-members',
      label: 'Builder Members',
      value: analytics.users_completed_all,
      sublabel: 'Completed all courses',
      visible: analytics.users_completed_all > 0,
    },
    {
      id: 'avg-completion',
      label: 'Average Completion Rate',
      value: `${analytics.average_completion_rate}%`,
      sublabel: 'Across engaged learners',
      visible: true,
    },
    {
      id: 'capstone-projects',
      label: 'Capstone Projects',
      value: analytics.total_capstone_submissions,
      sublabel: 'Total submissions',
      visible: true,
    },
    {
      id: 'active-sessions',
      label: 'Active Sessions',
      value: activeSessionsCount ?? 0,
      sublabel: 'Unique users online',
      onClick: openSessionsModal,
      visible: true,
    },
  ];

  return metrics.filter((m) => m.visible);
}

// ---------------------------------------------------------------------------
// Attention counts derivation
// ---------------------------------------------------------------------------

/**
 * Derives attention counts from various API responses. All returned values
 * are guaranteed to be non-negative integers.
 */
export function deriveAttentionCounts(
  submissions: CapstoneSubmissionsResponse | null,
  moduleHealth: ModuleHealthResponse | null,
  registryStatus: RegistryStatusResponse | null,
  pendingTestimonialCount: number
): AttentionCounts {
  return {
    pendingCapstones:
      submissions?.submissions?.filter((s) => s.status === 'pending')?.length ?? 0,
    pendingTestimonials: pendingTestimonialCount,
    moduleHealthIssues: moduleHealth?.validation_errors?.length ?? 0,
    registryIssues: registryStatus?.status === 'unavailable' ? 1 : 0,
  };
}

// ---------------------------------------------------------------------------
// Sorting utilities
// ---------------------------------------------------------------------------

/**
 * Returns a new array sorted by `percentage` in descending order
 * (monotonically non-increasing).
 */
export function sortByCompletionDesc<T extends { percentage: number }>(
  users: T[]
): T[] {
  return [...users].sort((a, b) => b.percentage - a.percentage);
}

/**
 * Returns a new array sorted by `registered_at` date string in descending
 * order (most recent first, monotonically non-increasing).
 */
export function sortByDateDesc<T extends { registered_at: string }>(
  members: T[]
): T[] {
  return [...members].sort(
    (a, b) =>
      new Date(b.registered_at).getTime() - new Date(a.registered_at).getTime()
  );
}
