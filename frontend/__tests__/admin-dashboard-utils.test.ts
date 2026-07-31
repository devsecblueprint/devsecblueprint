/**
 * Unit tests for admin dashboard pure utility functions.
 */

import {
  validateDateRange,
  buildKpiMetrics,
  deriveAttentionCounts,
  sortByCompletionDesc,
  sortByDateDesc,
} from '@/app/admin/components/utils';
import type { AnalyticsData } from '@/app/admin/components/types';
import type {
  CapstoneSubmissionsResponse,
  ModuleHealthResponse,
  RegistryStatusResponse,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// validateDateRange
// ---------------------------------------------------------------------------

describe('validateDateRange', () => {
  it('accepts a valid 30-day range', () => {
    const result = validateDateRange({
      startDate: '2024-01-01',
      endDate: '2024-01-31',
    });
    expect(result).toEqual({ valid: true });
  });

  it('rejects start date after end date', () => {
    const result = validateDateRange({
      startDate: '2024-06-15',
      endDate: '2024-06-01',
    });
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Start date must be before end date');
  });

  it('rejects range of less than 1 day (same date)', () => {
    const result = validateDateRange({
      startDate: '2024-03-10',
      endDate: '2024-03-10',
    });
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Minimum range is 1 day');
  });

  it('rejects range exceeding 365 days', () => {
    const result = validateDateRange({
      startDate: '2023-01-01',
      endDate: '2024-01-03',
    });
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Maximum range is 365 days');
  });

  it('rejects invalid date format', () => {
    const result = validateDateRange({
      startDate: 'not-a-date',
      endDate: '2024-01-01',
    });
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Invalid date format');
  });

  it('accepts exactly 1 day range', () => {
    const result = validateDateRange({
      startDate: '2024-05-01',
      endDate: '2024-05-02',
    });
    expect(result).toEqual({ valid: true });
  });

  it('accepts exactly 365 day range', () => {
    const result = validateDateRange({
      startDate: '2024-01-01',
      endDate: '2024-12-31',
    });
    expect(result).toEqual({ valid: true });
  });
});

// ---------------------------------------------------------------------------
// buildKpiMetrics
// ---------------------------------------------------------------------------

describe('buildKpiMetrics', () => {
  const baseAnalytics: AnalyticsData = {
    total_registered_users: 100,
    active_sessions: 5,
    users_with_progress: 80,
    users_completed_all: 10,
    total_completions: 50,
    average_completion_rate: 75,
    engagement_rate: 60,
    active_learners_7d: 25,
    total_capstone_submissions: 12,
    registration_timeline: [],
    completion_by_user: [],
  };

  const mockOpenModal = jest.fn();

  it('returns empty array when analytics is null', () => {
    expect(buildKpiMetrics(null, 3, mockOpenModal)).toEqual([]);
  });

  it('returns 6 metrics when all are visible', () => {
    const metrics = buildKpiMetrics(baseAnalytics, 3, mockOpenModal);
    expect(metrics).toHaveLength(6);
  });

  it('excludes Builder Members when users_completed_all is 0', () => {
    const analytics = { ...baseAnalytics, users_completed_all: 0 };
    const metrics = buildKpiMetrics(analytics, 3, mockOpenModal);
    expect(metrics).toHaveLength(5);
    expect(metrics.find((m) => m.id === 'builder-members')).toBeUndefined();
  });

  it('includes correct value for active sessions', () => {
    const metrics = buildKpiMetrics(baseAnalytics, 42, mockOpenModal);
    const sessionMetric = metrics.find((m) => m.id === 'active-sessions');
    expect(sessionMetric?.value).toBe(42);
  });

  it('defaults active sessions to 0 when null', () => {
    const metrics = buildKpiMetrics(baseAnalytics, null, mockOpenModal);
    const sessionMetric = metrics.find((m) => m.id === 'active-sessions');
    expect(sessionMetric?.value).toBe(0);
  });

  it('attaches onClick handler to active sessions metric', () => {
    const metrics = buildKpiMetrics(baseAnalytics, 3, mockOpenModal);
    const sessionMetric = metrics.find((m) => m.id === 'active-sessions');
    sessionMetric?.onClick?.();
    expect(mockOpenModal).toHaveBeenCalled();
  });

  it('formats average completion rate as percentage string', () => {
    const metrics = buildKpiMetrics(baseAnalytics, 3, mockOpenModal);
    const avgMetric = metrics.find((m) => m.id === 'avg-completion');
    expect(avgMetric?.value).toBe('75%');
  });
});

// ---------------------------------------------------------------------------
// deriveAttentionCounts
// ---------------------------------------------------------------------------

describe('deriveAttentionCounts', () => {
  it('returns all zeros when all inputs are null/zero', () => {
    const counts = deriveAttentionCounts(null, null, null, 0);
    expect(counts).toEqual({
      pendingCapstones: 0,
      pendingTestimonials: 0,
      moduleHealthIssues: 0,
      registryIssues: 0,
    });
  });

  it('counts pending capstone submissions', () => {
    const submissions: CapstoneSubmissionsResponse = {
      submissions: [
        { user_id: '1', content_id: 'm1', github_username: 'a', repo_url: '', submitted_at: '', updated_at: '', status: 'pending' },
        { user_id: '2', content_id: 'm2', github_username: 'b', repo_url: '', submitted_at: '', updated_at: '', status: 'approved' },
        { user_id: '3', content_id: 'm3', github_username: 'c', repo_url: '', submitted_at: '', updated_at: '', status: 'pending' },
      ],
      total_count: 3,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };
    const counts = deriveAttentionCounts(submissions, null, null, 0);
    expect(counts.pendingCapstones).toBe(2);
  });

  it('counts module health validation errors', () => {
    const moduleHealth: ModuleHealthResponse = {
      total_modules: 10,
      validation_pass_percentage: 80,
      content_by_type: { quiz: 3, module: 5, capstone: 1, walkthrough: 1 },
      validation_errors: [
        { module_id: 'm1', error_type: 'missing', error_message: 'Missing field' },
        { module_id: 'm2', error_type: 'invalid', error_message: 'Invalid format' },
      ],
      status: 'warning',
    };
    const counts = deriveAttentionCounts(null, moduleHealth, null, 0);
    expect(counts.moduleHealthIssues).toBe(2);
  });

  it('reports 1 registry issue when status is unavailable', () => {
    const registryStatus: RegistryStatusResponse = {
      schema_version: '1.0',
      last_updated: '2024-01-01',
      total_entries: 10,
      cache_status: 'loaded',
      cache_ttl_seconds: 300,
      cache_expires_in_seconds: 100,
      s3_bucket: 'bucket',
      s3_key: 'key',
      status: 'unavailable',
    };
    const counts = deriveAttentionCounts(null, null, registryStatus, 0);
    expect(counts.registryIssues).toBe(1);
  });

  it('reports 0 registry issues when status is healthy', () => {
    const registryStatus: RegistryStatusResponse = {
      schema_version: '1.0',
      last_updated: '2024-01-01',
      total_entries: 10,
      cache_status: 'loaded',
      cache_ttl_seconds: 300,
      cache_expires_in_seconds: 100,
      s3_bucket: 'bucket',
      s3_key: 'key',
      status: 'healthy',
    };
    const counts = deriveAttentionCounts(null, null, registryStatus, 0);
    expect(counts.registryIssues).toBe(0);
  });

  it('passes through pending testimonial count', () => {
    const counts = deriveAttentionCounts(null, null, null, 7);
    expect(counts.pendingTestimonials).toBe(7);
  });
});

// ---------------------------------------------------------------------------
// sortByCompletionDesc
// ---------------------------------------------------------------------------

describe('sortByCompletionDesc', () => {
  it('sorts users by percentage descending', () => {
    const users = [
      { percentage: 30 },
      { percentage: 90 },
      { percentage: 50 },
    ];
    const sorted = sortByCompletionDesc(users);
    expect(sorted.map((u) => u.percentage)).toEqual([90, 50, 30]);
  });

  it('does not mutate the original array', () => {
    const users = [{ percentage: 10 }, { percentage: 80 }];
    const original = [...users];
    sortByCompletionDesc(users);
    expect(users).toEqual(original);
  });

  it('handles empty array', () => {
    expect(sortByCompletionDesc([])).toEqual([]);
  });

  it('handles single element', () => {
    const result = sortByCompletionDesc([{ percentage: 42 }]);
    expect(result).toEqual([{ percentage: 42 }]);
  });
});

// ---------------------------------------------------------------------------
// sortByDateDesc
// ---------------------------------------------------------------------------

describe('sortByDateDesc', () => {
  it('sorts members by registered_at descending (most recent first)', () => {
    const members = [
      { registered_at: '2024-01-01T00:00:00Z' },
      { registered_at: '2024-06-15T00:00:00Z' },
      { registered_at: '2024-03-10T00:00:00Z' },
    ];
    const sorted = sortByDateDesc(members);
    expect(sorted.map((m) => m.registered_at)).toEqual([
      '2024-06-15T00:00:00Z',
      '2024-03-10T00:00:00Z',
      '2024-01-01T00:00:00Z',
    ]);
  });

  it('does not mutate the original array', () => {
    const members = [
      { registered_at: '2024-01-01T00:00:00Z' },
      { registered_at: '2024-12-01T00:00:00Z' },
    ];
    const original = [...members];
    sortByDateDesc(members);
    expect(members).toEqual(original);
  });

  it('handles empty array', () => {
    expect(sortByDateDesc([])).toEqual([]);
  });
});
