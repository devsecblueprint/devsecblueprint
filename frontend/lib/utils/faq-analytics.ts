/**
 * FAQ Analytics Utility
 *
 * Provides a fire-and-forget event emitter for tracking FAQ page interactions.
 * Wraps all logic in try-catch to guarantee non-blocking behavior — never throws,
 * never blocks rendering.
 */

export type FAQAnalyticsEvent =
  | { type: 'category_selected'; categorySlug: string }
  | { type: 'question_expanded'; questionSlug: string; categorySlug: string }
  | { type: 'search_performed'; query: string; resultCount: number }
  | { type: 'search_no_results'; query: string }
  | { type: 'copy_link'; questionSlug: string };

/**
 * Track an FAQ interaction event.
 *
 * This function is fire-and-forget: it never throws and never blocks rendering.
 * In development, events are logged to the console. In production, this integrates
 * with the configured analytics provider (stub — replace with GA4, PostHog, etc.).
 */
export function trackFAQEvent(event: FAQAnalyticsEvent): void {
  try {
    if (process.env.NODE_ENV === 'development') {
      // eslint-disable-next-line no-console
      console.debug('[FAQ Analytics]', event.type, event);
      return;
    }

    // Production: integrate with analytics provider here.
    // Example stubs for common providers:
    //
    // Google Analytics 4:
    //   window.gtag?.('event', event.type, eventToParams(event));
    //
    // PostHog:
    //   window.posthog?.capture(event.type, eventToParams(event));
    //
    // For now, this is a no-op in production until a provider is configured.
    void event;
  } catch {
    // Swallow all errors — analytics must never disrupt the user experience.
  }
}
