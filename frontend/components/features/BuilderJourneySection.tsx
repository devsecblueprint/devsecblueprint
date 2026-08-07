'use client';

import { useEffect } from 'react';
import {
  BUILDER_JOURNEY_PHASES,
  BUILDER_JOURNEY_SECTION,
} from '@/lib/data/builder-journey';
import type { BuilderJourneyPhase } from '@/lib/data/builder-journey';
import { trackJourneyEvent } from '@/lib/utils/journey-analytics';

/**
 * Public-facing Builder Journey section for the homepage.
 * Presents a visual overview of the five onboarding phases with a CTA.
 * Informational only — no personalized progress or dashboard functionality.
 */
export function BuilderJourneySection() {
  useEffect(() => {
    trackJourneyEvent({ type: 'journey_section_viewed' });
  }, []);

  return (
    <section
      aria-label="Builder Journey onboarding phases"
      className="px-4 sm:px-6 py-12 sm:py-16 md:py-20 bg-gray-50 dark:bg-gray-900/50"
    >
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 dark:text-gray-100 text-center mb-4">
          {BUILDER_JOURNEY_SECTION.title}
        </h2>
        <p className="text-base text-gray-600 dark:text-gray-400 text-center max-w-3xl mx-auto mb-4 leading-relaxed">
          {BUILDER_JOURNEY_SECTION.subtitle}
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-500 text-center max-w-2xl mx-auto mb-10 sm:mb-14">
          {BUILDER_JOURNEY_SECTION.note}
        </p>

        {/* Phase timeline */}
        <div className="relative">
          {/* Vertical connector line (visible on md+) */}
          <div
            className="hidden md:block absolute left-1/2 top-0 bottom-0 w-px bg-gray-200 dark:bg-gray-700 -translate-x-1/2"
            aria-hidden="true"
          />

          <ol className="space-y-8 md:space-y-12 relative">
            {BUILDER_JOURNEY_PHASES.map((phase, index) => (
              <PhaseCard key={phase.phase} phase={phase} index={index} />
            ))}
          </ol>
        </div>

        {/* CTA */}
        <div className="text-center mt-12 sm:mt-16">
          <a
            href={BUILDER_JOURNEY_SECTION.cta.href}
            className="inline-flex items-center justify-center px-6 py-3 text-base font-semibold rounded-lg bg-primary-400 text-gray-900 hover:bg-primary-500 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 focus:ring-offset-gray-50 dark:focus:ring-offset-gray-900 min-h-[44px] min-w-[44px]"
          >
            {BUILDER_JOURNEY_SECTION.cta.label}
            <svg
              className="w-5 h-5 ml-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M14 5l7 7m0 0l-7 7m7-7H3"
              />
            </svg>
          </a>
        </div>
      </div>
    </section>
  );
}

function PhaseCard({ phase, index }: { phase: BuilderJourneyPhase; index: number }) {
  const isEven = index % 2 === 0;

  return (
    <li className="relative md:grid md:grid-cols-2 md:gap-8 items-start">
      {/* Center dot (md+) */}
      <div
        className="hidden md:flex absolute left-1/2 -translate-x-1/2 top-6 w-10 h-10 rounded-full bg-primary-400 text-gray-900 font-bold text-sm items-center justify-center z-10 shadow-sm"
        aria-hidden="true"
      >
        {phase.phase}
      </div>

      {/* Card — alternates sides on desktop */}
      <div
        className={`md:col-span-1 ${isEven ? 'md:col-start-1 md:pr-12' : 'md:col-start-2 md:pl-12'}`}
      >
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
          {/* Mobile phase number + icon */}
          <div className="flex items-center gap-3 mb-3">
            <span className="md:hidden flex w-8 h-8 rounded-full bg-primary-400 text-gray-900 font-bold text-xs items-center justify-center flex-shrink-0">
              {phase.phase}
            </span>
            <PhaseIcon icon={phase.icon} />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {phase.title}
            </h3>
          </div>

          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 leading-relaxed">
            {phase.objective}
          </p>

          {/* Task list preview */}
          <ul className="space-y-1.5">
            {phase.tasks.slice(0, 4).map((task) => (
              <li key={task.title} className="flex items-start gap-2 text-sm text-gray-500 dark:text-gray-400">
                <svg
                  className="w-4 h-4 text-primary-400 flex-shrink-0 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4"
                  />
                </svg>
                <span>{task.title}</span>
              </li>
            ))}
            {phase.tasks.length > 4 && (
              <li className="text-xs text-gray-400 dark:text-gray-500 pl-6">
                +{phase.tasks.length - 4} more
              </li>
            )}
          </ul>

          {/* Outcome */}
          <p className="mt-4 text-xs text-gray-500 dark:text-gray-500 italic leading-relaxed">
            {phase.outcome}
          </p>
        </div>
      </div>

      {/* Empty column for alternating layout (md+) */}
      {isEven ? (
        <div className="hidden md:block md:col-start-2" aria-hidden="true" />
      ) : (
        <div className="hidden md:block md:col-start-1" aria-hidden="true" />
      )}
    </li>
  );
}

function PhaseIcon({ icon }: { icon: BuilderJourneyPhase['icon'] }) {
  const className = 'w-5 h-5 text-primary-500 dark:text-primary-400 flex-shrink-0';

  switch (icon) {
    case 'welcome':
      return (
        <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
        </svg>
      );
    case 'community':
      return (
        <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
        </svg>
      );
    case 'foundation':
      return (
        <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      );
    case 'path':
      return (
        <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 6.75V15m0 0l3-3m-3 3l-3-3m12-3V6a2.25 2.25 0 00-2.25-2.25H6.75A2.25 2.25 0 004.5 6v.75m15 0H4.5m15 0v9A2.25 2.25 0 0117.25 18H6.75A2.25 2.25 0 014.5 15.75v-9" />
        </svg>
      );
    case 'momentum':
      return (
        <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
        </svg>
      );
  }
}
