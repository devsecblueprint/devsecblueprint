/**
 * Unit tests for the admin dashboard pure utilities.
 */
import {
  validateDateRange,
  buildKpiMetrics,
  deriveAttentionCounts,
  sortByCompletionDesc,
  sortByDateDesc,
} from '@/app/admin/components/utils';

describe('validateDateRange', () => {
  it('accepts a valid range', () => {
    expect(validateDateRange({ startDate: '2026-01-01', endDate: '2026-01-15' })).toEqual({ valid: true });
  });

  it('rejects invalid date formats', () => {
    const r = validateDateRange({ startDate: 'nope', endDate: '2026-01-01' });
    expect(r.valid).toBe(false);
    expect(r.error).toMatch(/Invalid date format/);
  });

  it('rejects start after end', () => {
    const r = validateDateRange({ startDate: '2026-02-01', endDate: '2026-01-01' });
    expect(r.valid).toBe(false);
    expect(r.error).toMatch(/before end date/);
  });

  it('rejects a zero-day span', () => {
    const r = validateDateRange({ startDate: '2026-01-01', endDate: '2026-01-01' });
    expect(r.valid).toBe(false);
    expect(r.error).toMatch(/Minimum range/);
  });

  it('rejects spans over 365 days', () => {
    const r = validateDateRange({ startDate: '2024-01-01', endDate: '2026-01-01' });
    expect(r.valid).toBe(false);
    expect(r.error).toMatch(/Maximum range/);
  });
});

describe('buildKpiMetrics', () => {
  const analytics = {
    total_registered_users: 100,
    active_learners_7d: 20,
    users_completed_all: 5,
    average_completion_rate: 42,
    total_capstone_submissions: 8,
  } as never;

  it('returns an empty array when analytics is null', () => {
    expect(buildKpiMetrics(null, 0, jest.fn())).toEqual([]);
  });

  it('builds all visible metrics', () => {
    const metrics = buildKpiMetrics(analytics, 3, jest.fn());
    const ids = metrics.map((m) => m.id);
    expect(ids).toContain('total-users');
    expect(ids).toContain('builder-members');
    expect(ids).toContain('active-sessions');
  });

  it('hides builder-members when none have completed all', () => {
    const metrics = buildKpiMetrics({ ...analytics, users_completed_all: 0 } as never, 0, jest.fn());
    expect(metrics.map((m) => m.id)).not.toContain('builder-members');
  });
});

describe('deriveAttentionCounts', () => {
  it('derives non-negative counts from mixed inputs', () => {
    const counts = deriveAttentionCounts(
      { submissions: [{ status: 'pending' }, { status: 'reviewed' }] } as never,
      { validation_errors: [{}, {}] } as never,
      { status: 'unavailable' } as never,
      3,
    );
    expect(counts).toEqual({
      pendingCapstones: 1,
      pendingTestimonials: 3,
      moduleHealthIssues: 2,
      registryIssues: 1,
    });
  });

  it('defaults to zeros when inputs are null', () => {
    expect(deriveAttentionCounts(null, null, null, 0)).toEqual({
      pendingCapstones: 0,
      pendingTestimonials: 0,
      moduleHealthIssues: 0,
      registryIssues: 0,
    });
  });
});

describe('sorting utilities', () => {
  it('sorts by completion percentage descending', () => {
    const result = sortByCompletionDesc([{ percentage: 10 }, { percentage: 90 }, { percentage: 50 }]);
    expect(result.map((r) => r.percentage)).toEqual([90, 50, 10]);
  });

  it('does not mutate the input array', () => {
    const input = [{ percentage: 1 }, { percentage: 2 }];
    sortByCompletionDesc(input);
    expect(input.map((r) => r.percentage)).toEqual([1, 2]);
  });

  it('sorts by registered date descending', () => {
    const result = sortByDateDesc([
      { registered_at: '2026-01-01' },
      { registered_at: '2026-03-01' },
      { registered_at: '2026-02-01' },
    ]);
    expect(result.map((r) => r.registered_at)).toEqual(['2026-03-01', '2026-02-01', '2026-01-01']);
  });
});
