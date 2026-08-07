/**
 * Journey Analytics Event Emitter
 *
 * Fire-and-forget analytics abstraction for Builder Journey events.
 * Currently logs to console in development and no-ops in production.
 * Swap the implementation for a real analytics provider when ready.
 */

import type { JourneyTier } from '@/lib/data/builder-journey';

export type JourneyAnalyticsEvent =
  | { type: 'journey_started'; userId: string; tier: JourneyTier }
  | { type: 'task_completed'; taskId: string; phaseId: number; timestamp: string; tier: JourneyTier }
  | { type: 'phase_completed'; phaseId: number; durationDays: number; tier: JourneyTier }
  | { type: 'journey_completed'; totalDurationDays: number; tier: JourneyTier }
  | { type: 'journey_section_viewed' };

/**
 * Emit a Builder Journey analytics event.
 *
 * This function is fire-and-forget — it will never throw or block
 * UI rendering regardless of analytics provider availability.
 */
export function trackJourneyEvent(event: JourneyAnalyticsEvent): void {
  try {
    if (process.env.NODE_ENV === 'development') {
      // eslint-disable-next-line no-console
      console.log('[JourneyAnalytics]', event.type, event);
    }
    // Production: no-op placeholder.
    // Replace this block with your analytics provider call, e.g.:
    // analyticsProvider.track(event.type, event);
  } catch {
    // Silently swallow errors — analytics must never break the UI.
  }
}
