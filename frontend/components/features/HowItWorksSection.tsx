'use client';

import type { ReactNode } from 'react';

interface JourneyStep {
  label: string;
  description: string;
  icon: ReactNode;
}

const iconClassName = 'w-7 h-7';

const JOURNEY_STEPS: JourneyStep[] = [
  {
    label: 'LEARN',
    description:
      'Develop the foundations behind DevSecOps, cloud security, secure software delivery, and security engineering.',
    icon: (
      <svg className={iconClassName} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
  },
  {
    label: 'BUILD',
    description:
      'Turn concepts into working systems through guided walkthroughs, projects, and real infrastructure.',
    icon: (
      <svg className={iconClassName} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11.42 15.17l-5.1-5.1m0 0L3.5 12.89m2.82-2.82L3.5 7.25M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-4.75-2.5a.75.75 0 100-1.5.75.75 0 000 1.5z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11.42 15.17L13.5 17.25l3.18-3.18" />
      </svg>
    ),
  },
  {
    label: 'APPLY',
    description:
      'Solve practical engineering problems through projects and capstones designed to test your ability to apply what you\u2019ve learned.',
    icon: (
      <svg className={iconClassName} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
      </svg>
    ),
  },
  {
    label: 'GROW',
    description:
      'Learn alongside other builders, receive guidance and feedback, strengthen your career, and continue developing as an engineer.',
    icon: (
      <svg className={iconClassName} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
      </svg>
    ),
  },
];

/**
 * "How The DevSec Blueprint Works" section.
 * Presents a four-step progression: Learn → Build → Apply → Grow.
 * Horizontal cards on desktop, stacked vertically on mobile.
 */
export function HowItWorksSection() {
  return (
    <section
      aria-labelledby="how-it-works-heading"
      className="px-4 sm:px-6 py-16 sm:py-20 md:py-24 bg-gray-50 dark:bg-gray-900/50"
    >
      <div className="max-w-6xl mx-auto">
        {/* Section header */}
        <h2
          id="how-it-works-heading"
          className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 dark:text-gray-100 text-center mb-4"
        >
          How The DevSec Blueprint Works
        </h2>
        <p className="text-base sm:text-lg text-gray-600 dark:text-gray-400 text-center max-w-3xl mx-auto mb-12 sm:mb-16 leading-relaxed">
          DSB provides a structured path for developing practical security engineering
          skills—not simply consuming educational content.
        </p>

        {/* Desktop: horizontal cards with arrows */}
        <div className="hidden md:grid md:grid-cols-4 gap-6 lg:gap-8">
          {JOURNEY_STEPS.map((step, index) => (
            <div key={step.label} className="relative flex flex-col items-center text-center">
              {/* Arrow connector between cards */}
              {index < JOURNEY_STEPS.length - 1 && (
                <div
                  className="absolute top-10 -right-3 lg:-right-4 text-primary-400 dark:text-primary-500"
                  aria-hidden="true"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="w-5 h-5 lg:w-6 lg:h-6"
                  >
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </div>
              )}

              {/* Icon circle */}
              <div className="flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 mb-4">
                {step.icon}
              </div>

              {/* Step label */}
              <span className="text-xs font-bold tracking-widest uppercase text-primary-500 dark:text-primary-400 mb-2">
                {step.label}
              </span>

              {/* Description */}
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                {step.description}
              </p>
            </div>
          ))}
        </div>

        {/* Mobile: vertical stacked cards with progression line */}
        <div className="md:hidden space-y-8 relative">
          {/* Vertical progress line */}
          <div
            className="absolute left-5 top-0 bottom-0 w-0.5 bg-primary-200 dark:bg-primary-800"
            aria-hidden="true"
          />

          {JOURNEY_STEPS.map((step) => (
            <div key={step.label} className="relative flex gap-4">
              {/* Icon circle on the line */}
              <div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 z-10">
                {step.icon}
              </div>

              {/* Content */}
              <div className="pt-1">
                <span className="text-xs font-bold tracking-widest uppercase text-primary-500 dark:text-primary-400">
                  {step.label}
                </span>
                <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed mt-1">
                  {step.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
