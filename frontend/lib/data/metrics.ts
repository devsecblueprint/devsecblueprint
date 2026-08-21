/**
 * Centralized Public Metrics
 *
 * Single source of truth for all publicly displayed community and platform metrics.
 * Any component or page that displays these numbers should import from this file
 * rather than hard-coding values.
 *
 * Metrics reflect January–August 2026 data sourced from Google Analytics.
 * Active Users reflects unique visitors who engaged with the platform.
 * All growth is organic — no paid advertising.
 */

export interface PublicMetric {
  /** Display value (e.g., "13K+") */
  value: string;
  /** Label describing the metric */
  label: string;
}

// ─── Core Platform Metrics ────────────────────────────────────────────────────

export const METRIC_ACTIVE_USERS: PublicMetric = {
  value: '13K+',
  label: 'Active Users',
};

export const METRIC_CONTENT_VIEWS: PublicMetric = {
  value: '51K+',
  label: 'Content Views',
};

export const METRIC_PLATFORM_EVENTS: PublicMetric = {
  value: '124K+',
  label: 'Platform Events',
};

export const METRIC_LINKEDIN_FOLLOWERS: PublicMetric = {
  value: '1,100+',
  label: 'LinkedIn Followers',
};

export const METRIC_ORGANIC_IMPRESSIONS: PublicMetric = {
  value: '10,000+',
  label: 'Organic Impressions',
};

export const METRIC_UNIQUE_ORGANIC_IMPRESSIONS: PublicMetric = {
  value: '7,000+',
  label: 'Unique Organic Impressions',
};

export const METRIC_CLICKS_ENGAGEMENTS: PublicMetric = {
  value: '400+',
  label: 'Clicks and Social Engagements',
};

// ─── Disclosure ───────────────────────────────────────────────────────────────

export const METRICS_DISCLOSURE =
  'Platform metrics reflect January–August 2026 data sourced from Google Analytics. Active Users reflects unique visitors who engaged with the platform. All growth is organic — no paid advertising.';
