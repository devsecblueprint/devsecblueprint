'use client';

import { COMPANIES } from '@/lib/data/companies';

/**
 * Infinite-scroll marquee carousel displaying company logos
 * where DSB members have landed roles and internships.
 *
 * The logos are duplicated to create a seamless loop effect.
 * Animation pauses on hover for accessibility.
 */
export function CompanyCarousel() {
  // Don't render if no companies configured
  if (COMPANIES.length === 0) return null;

  const useMarquee = COMPANIES.length >= 5;

  // Duplicate the list to create the seamless infinite loop
  const logos = useMarquee ? [...COMPANIES, ...COMPANIES] : COMPANIES;

  return (
    <section
      className="px-4 sm:px-6 py-12 sm:py-16 md:py-24 bg-white dark:bg-gray-950"
      aria-label="Companies where DSB members have landed"
    >
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 dark:text-gray-100 text-center mb-3">
          Companies Where DSB Members Have Landed
        </h2>
        <p className="text-gray-500 dark:text-gray-400 text-center text-sm sm:text-base mb-10">
          Member outcomes include roles and internships at companies such as&hellip;
        </p>

        {useMarquee ? (
          /* Marquee mode: infinite scroll when 5+ logos */
          <div className="relative overflow-hidden">
            {/* Gradient fade edges */}
            <div className="pointer-events-none absolute inset-y-0 left-0 w-16 sm:w-24 bg-gradient-to-r from-white dark:from-gray-950 to-transparent z-10" />
            <div className="pointer-events-none absolute inset-y-0 right-0 w-16 sm:w-24 bg-gradient-to-l from-white dark:from-gray-950 to-transparent z-10" />

            {/* Scrolling track */}
            <div
              className="flex items-center gap-12 sm:gap-16 md:gap-20 animate-marquee hover:[animation-play-state:paused]"
              style={{ width: 'max-content' }}
            >
              {logos.map((company, index) => (
                <div
                  key={`${company.name}-${index}`}
                  className="flex-shrink-0 flex items-center justify-center h-12 sm:h-14"
                >
                  {company.url ? (
                    <a
                      href={company.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label={`${company.name} (opens in new tab)`}
                      className="transition-opacity opacity-70 hover:opacity-100"
                    >
                      <img
                        src={company.logoUrl}
                        alt={company.name}
                        className="h-8 sm:h-10 md:h-12 w-auto object-contain"
                        loading="lazy"
                      />
                    </a>
                  ) : (
                    <img
                      src={company.logoUrl}
                      alt={company.name}
                      className="h-8 sm:h-10 md:h-12 w-auto object-contain opacity-70"
                      loading="lazy"
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* Static centered mode: larger logos when fewer than 5 */
          <div className="flex items-center justify-center flex-wrap gap-10 sm:gap-14 md:gap-20">
            {logos.map((company) => (
              <div
                key={company.name}
                className="flex items-center justify-center"
              >
                {company.url ? (
                  <a
                    href={company.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={`${company.name} (opens in new tab)`}
                    className="transition-opacity opacity-80 hover:opacity-100"
                  >
                    <img
                      src={company.logoUrl}
                      alt={company.name}
                      className="h-12 sm:h-16 md:h-20 w-auto object-contain"
                      loading="lazy"
                    />
                  </a>
                ) : (
                  <img
                    src={company.logoUrl}
                    alt={company.name}
                    className="h-12 sm:h-16 md:h-20 w-auto object-contain opacity-80"
                    loading="lazy"
                  />
                )}
              </div>
            ))}
          </div>
        )}

        {/* Disclaimer */}
        <p className="text-gray-400 dark:text-gray-500 text-center text-xs mt-8">
          Company names and logos are shown to highlight member outcomes and do not imply endorsement or partnership.
        </p>
      </div>
    </section>
  );
}
