import { getNavigatorInterestFormUrl } from './NavigatorTeaser';

/**
 * The four Navigator feature highlights shown in the featured pricing band.
 * Icons are inline SVGs to match the project's icon convention (no icon lib).
 */
const FEATURES: { label: string; icon: React.ReactNode }[] = [
  {
    label: '12-week mentorship experience',
    icon: (
      <svg
        className="w-5 h-5"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
        />
      </svg>
    ),
  },
  {
    label: 'Personalized development roadmap',
    icon: (
      <svg
        className="w-5 h-5"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
        />
      </svg>
    ),
  },
  {
    label: 'Technical and career guidance',
    icon: (
      <svg
        className="w-5 h-5"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
        />
      </svg>
    ),
  },
  {
    label: 'Limited founding cohort',
    icon: (
      <svg
        className="w-5 h-5"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m6-1.13a4 4 0 10-4-4 4 4 0 004 4zm6 1a3 3 0 10-2-5.24M5 9a3 3 0 102 5.24"
        />
      </svg>
    ),
  },
];

/**
 * Featured DSB Navigator offering for the pricing page.
 *
 * This is a program-discovery and interest-list conversion band only. It does
 * not create a Stripe product, checkout, subscription, or enrollment flow. The
 * CTA opens the externally hosted Google Form (shared via
 * NEXT_PUBLIC_NAVIGATOR_INTEREST_FORM_URL, the same source the homepage
 * NavigatorTeaser uses) in a new tab. When the URL is missing/invalid the CTA
 * is hidden, consistent with NavigatorTeaser.
 */
export function NavigatorFeature() {
  const formUrl = getNavigatorInterestFormUrl();

  if (!formUrl && typeof window !== 'undefined') {
    console.warn(
      'NEXT_PUBLIC_NAVIGATOR_INTEREST_FORM_URL is not set or is not a valid Google Forms responder URL. The Navigator CTA is hidden.'
    );
  }

  return (
    <section
      aria-labelledby="navigator-feature-heading"
      className="max-w-7xl mx-auto mb-20"
    >
      <div className="relative overflow-hidden rounded-3xl bg-gray-950 border border-primary-400/60 shadow-[0_0_40px_-12px_rgba(255,190,0,0.35)] px-6 sm:px-10 lg:px-14 py-10 sm:py-12">
        <div className="grid grid-cols-1 lg:grid-cols-[auto_1fr_auto] gap-8 lg:gap-10 items-center">
          {/* Navigator compass emblem (decorative) */}
          <div className="hidden sm:flex justify-center lg:justify-start">
            <span className="flex items-center justify-center w-20 h-20 lg:w-24 lg:h-24 rounded-2xl bg-primary-400/10 border border-primary-400/40">
              <img
                src="/images/dsb-navigator.png"
                alt=""
                className="w-12 h-12 lg:w-14 lg:h-14"
                width={1254}
                height={1254}
                loading="lazy"
              />
            </span>
          </div>

          {/* Program information */}
          <div className="space-y-4 lg:border-r lg:border-gray-800 lg:pr-10">
            <p className="text-xs sm:text-sm font-semibold tracking-widest uppercase text-primary-400">
              Coming Soon · DSB Navigator
            </p>
            <h2
              id="navigator-feature-heading"
              className="text-2xl sm:text-3xl lg:text-4xl font-bold text-white"
            >
              Your next move deserves a blueprint.
            </h2>
            <p className="text-base text-gray-300 leading-relaxed max-w-2xl">
              Personalized engineering and career mentorship for individuals
              pursuing growth in DevSecOps and Cloud Security Engineering.
            </p>

            {/* Feature highlights: compact row on desktop, 2-col on tablet,
                single column on mobile. */}
            <ul
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-x-6 gap-y-4 pt-2"
              aria-label="DSB Navigator program highlights"
            >
              {FEATURES.map((feature) => (
                <li key={feature.label} className="flex items-start gap-3">
                  <span className="shrink-0 text-primary-400" aria-hidden="true">
                    {feature.icon}
                  </span>
                  <span className="text-sm text-gray-200 leading-snug">
                    {feature.label}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          {/* CTA + disclaimer */}
          <div className="space-y-4 lg:max-w-xs">
            {formUrl ? (
              <a
                href={formUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex w-full items-center justify-center gap-2 px-6 py-4 text-base font-semibold rounded-xl bg-primary-400 text-gray-900 hover:bg-primary-500 transition-colors focus:outline-hidden focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 focus:ring-offset-gray-950 min-h-[48px]"
              >
                Join the Interest List
                <svg
                  className="w-4 h-4"
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
                <span className="sr-only"> (opens in a new tab)</span>
              </a>
            ) : null}
            <p className="text-xs text-gray-400 leading-relaxed">
              We&apos;re still finalizing program details and logistics.
              Applications are not open. Joining the list does not guarantee
              admission or require payment.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
