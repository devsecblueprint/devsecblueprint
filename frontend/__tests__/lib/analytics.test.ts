/**
 * Unit tests for the fire-and-forget analytics emitters.
 * Both must never throw and must respect the dev/prod branch.
 */
import { trackFAQEvent } from '@/lib/utils/faq-analytics';
import { trackJourneyEvent } from '@/lib/utils/journey-analytics';

const ORIGINAL_ENV = process.env.NODE_ENV;

function setNodeEnv(value: string) {
  // NODE_ENV is read-only in types; override via defineProperty for the test.
  Object.defineProperty(process.env, 'NODE_ENV', { value, configurable: true });
}

afterEach(() => {
  setNodeEnv(ORIGINAL_ENV as string);
  jest.restoreAllMocks();
});

describe('trackFAQEvent', () => {
  it('logs to console.debug in development', () => {
    const spy = jest.spyOn(console, 'debug').mockImplementation(() => {});
    setNodeEnv('development');
    trackFAQEvent({ type: 'category_selected', categorySlug: 'general' });
    expect(spy).toHaveBeenCalledWith('[FAQ Analytics]', 'category_selected', expect.any(Object));
  });

  it('is a silent no-op in production', () => {
    const spy = jest.spyOn(console, 'debug').mockImplementation(() => {});
    setNodeEnv('production');
    trackFAQEvent({ type: 'search_performed', query: 'iam', resultCount: 3 });
    expect(spy).not.toHaveBeenCalled();
  });

  it('never throws for any event shape', () => {
    setNodeEnv('production');
    expect(() => {
      trackFAQEvent({ type: 'search_no_results', query: 'zzz' });
      trackFAQEvent({ type: 'question_expanded', questionSlug: 'q1', categorySlug: 'c1' });
      trackFAQEvent({ type: 'copy_link', questionSlug: 'q1' });
    }).not.toThrow();
  });
});

describe('trackJourneyEvent', () => {
  it('logs to console.log in development', () => {
    const spy = jest.spyOn(console, 'log').mockImplementation(() => {});
    setNodeEnv('development');
    trackJourneyEvent({ type: 'journey_section_viewed' });
    expect(spy).toHaveBeenCalledWith('[JourneyAnalytics]', 'journey_section_viewed', expect.any(Object));
  });

  it('does not log in production', () => {
    const spy = jest.spyOn(console, 'log').mockImplementation(() => {});
    setNodeEnv('production');
    trackJourneyEvent({ type: 'journey_started', userId: 'u1', tier: 'free' as never });
    expect(spy).not.toHaveBeenCalled();
  });

  it('never throws across event variants', () => {
    setNodeEnv('development');
    jest.spyOn(console, 'log').mockImplementation(() => {});
    expect(() => {
      trackJourneyEvent({ type: 'task_completed', taskId: 't', phaseId: 1, timestamp: 'now', tier: 'free' as never });
      trackJourneyEvent({ type: 'phase_completed', phaseId: 1, durationDays: 3, tier: 'free' as never });
      trackJourneyEvent({ type: 'journey_completed', totalDurationDays: 30, tier: 'free' as never });
    }).not.toThrow();
  });
});
