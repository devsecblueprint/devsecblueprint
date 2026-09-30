'use client';

import { COMPANIES, type Company } from '@/lib/data/companies';

/**
 * Continuously scrolling showcase of companies where DSB members have landed.
 *
 * Each logo sits inside a uniform light "tile" card so marks stay legible
 * regardless of their color or the section's theme, and different logo aspect
 * ratios are normalized into the same box. The track scrolls in one continuous
 * motion via a CSS marquee animation; the list is duplicated so the loop is
 * seamless, and the motion pauses on hover.
 */
export function CompanyCarousel() {
  // Don't render if no companies are configured.
  if (COMPANIES.length === 0) return null;

  return (
    <section
      className="px-4 sm:px-6 py-12 sm:py-16 md:py-24 bg-white dark:bg-gray-950"
      aria-label="Companies where DSB members have landed"
    >
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="max-w-3xl mx-auto text-center mb-12">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-3">
            Companies Where DSB Members Have Landed
          </h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm sm:text-base">
            Member outcomes include roles and internships at companies such as&hellip;
          </p>
          <div className="mt-4 h-1 w-20 rounded-full bg-primary-400 dark:bg-primary-500 mx-auto" aria-hidden="true" />
        </div>

        {/* Marquee */}
        <div className="group relative overflow-hidden">
          {/* Edge fades */}
          <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-16 bg-gradient-to-r from-white dark:from-gray-950 to-transparent" aria-hidden="true" />
          <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-16 bg-gradient-to-l from-white dark:from-gray-950 to-transparent" aria-hidden="true" />

          {/* Continuously scrolling track. The list is rendered twice so the
              -50% translation loops seamlessly; the animation pauses on hover. */}
          <div className="flex w-max gap-6 animate-marquee group-hover:[animation-play-state:paused] py-2">
            {COMPANIES.map((company) => (
              <CompanyTile key={`a-${company.name}`} company={company} />
            ))}
            {/* Duplicate for a seamless loop; hidden from assistive tech. */}
            {COMPANIES.map((company) => (
              <CompanyTile key={`b-${company.name}`} company={company} ariaHidden />
            ))}
          </div>
        </div>

        {/* Disclaimer */}
        <p className="text-gray-400 dark:text-gray-500 text-center text-xs mt-8">
          Company names and logos are shown to highlight member outcomes and do not imply endorsement or partnership.
        </p>
      </div>
    </section>
  );
}

function CompanyTile({ company, ariaHidden = false }: { company: Company; ariaHidden?: boolean }) {
  const tile = (
    <div className="group/tile relative aspect-[3/2] rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 ring-1 ring-black/5 dark:ring-white/10 shadow-md hover:shadow-xl transition-shadow duration-300 overflow-hidden">
      {company.logoUrl ? (
        <div className="flex h-full w-full items-center justify-center p-8">
          <img
            src={company.logoUrl}
            alt={`${company.name} logo`}
            className="max-h-full max-w-full object-contain transition-transform duration-300 group-hover/tile:scale-110"
            loading="lazy"
          />
        </div>
      ) : (
        <div className="flex h-full w-full items-center justify-center p-8">
          <span className="text-xl font-semibold text-gray-900 text-center transition-transform duration-300 group-hover/tile:scale-110">
            {company.name}
          </span>
        </div>
      )}
      {/* Hover overlay with company name */}
      <div className="absolute inset-0 flex items-center justify-center bg-black/55 opacity-0 group-hover/tile:opacity-100 transition-opacity duration-300">
        <p className="px-4 text-center font-semibold text-white translate-y-3 group-hover/tile:translate-y-0 transition-transform duration-300">
          {company.name}
        </p>
      </div>
    </div>
  );

  return (
    <div className="flex-none w-56 sm:w-64 md:w-72" aria-hidden={ariaHidden || undefined}>
      {company.url ? (
        <a
          href={company.url}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={`${company.name} (opens in a new tab)`}
          tabIndex={ariaHidden ? -1 : undefined}
          className="block rounded-2xl focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-400 dark:focus-visible:ring-primary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-gray-950"
        >
          {tile}
        </a>
      ) : (
        tile
      )}
    </div>
  );
}
