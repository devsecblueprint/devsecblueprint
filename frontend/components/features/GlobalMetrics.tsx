'use client';

import dynamic from 'next/dynamic';
import { HOMEPAGE_METRICS, HOMEPAGE_METRICS_DISCLOSURE } from '@/lib/data/homepage';
import type { HomepageMetric } from '@/lib/data/homepage';

// Dynamically import Globe3D to avoid SSR issues with Three.js
const Globe3D = dynamic(
  () => import('./Globe3D').then((mod) => ({ default: mod.Globe3D })),
  { ssr: false, loading: () => <GlobePlaceholder /> }
);

/**
 * Global community metrics section.
 * Two-column layout: 3D rotating globe (left) + metrics (right).
 * On mobile: globe first, metrics stacked beneath.
 */
export function GlobalMetrics() {
  return (
    <section className="px-4 sm:px-6 py-12 sm:py-16 md:py-20 bg-white dark:bg-gray-950">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 dark:text-gray-100 text-center mb-4">
          Built for a Global Community
        </h2>
        <p className="text-base text-gray-600 dark:text-gray-400 text-center max-w-2xl mx-auto mb-10 sm:mb-14 leading-relaxed">
          The DevSec Blueprint reaches engineers, security practitioners, and technical
          builders across more than 140 countries.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-16 items-center">
          {/* Left — 3D Globe */}
          <div className="flex justify-center">
            <Globe3D />
          </div>

          {/* Right — Metrics */}
          <div className="space-y-8">
            {HOMEPAGE_METRICS.map((metric) => (
              <MetricRow key={metric.label} metric={metric} />
            ))}
          </div>
        </div>

        {/* Disclosure */}
        <p className="text-xs text-gray-500 dark:text-gray-500 text-center max-w-2xl mx-auto mt-10 leading-relaxed">
          {HOMEPAGE_METRICS_DISCLOSURE}
        </p>
      </div>
    </section>
  );
}

function MetricRow({ metric }: { metric: HomepageMetric }) {
  return (
    <div className="flex items-center gap-4">
      <MetricIcon icon={metric.icon} />
      <div>
        <span className="block text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100">
          {metric.value}
        </span>
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {metric.label}
        </span>
      </div>
    </div>
  );
}

function MetricIcon({ icon }: { icon: HomepageMetric['icon'] }) {
  const className = 'w-10 h-10 text-primary-500 dark:text-primary-400 flex-shrink-0';

  switch (icon) {
    case 'users':
      return (
        <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
        </svg>
      );
    case 'views':
      return (
        <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      );
    case 'events':
      return (
        <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" />
        </svg>
      );
    case 'linkedin':
      return (
        <svg className={className} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
        </svg>
      );
  }
}
function GlobePlaceholder() {
  return (
    <div className="w-full aspect-square max-w-[320px] sm:max-w-[360px] mx-auto flex items-center justify-center">
      <div className="w-48 h-48 rounded-full border-2 border-gray-200 dark:border-gray-700 border-dashed animate-pulse" />
    </div>
  );
}
