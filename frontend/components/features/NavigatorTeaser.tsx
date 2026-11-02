/**
 * Returns the published Google Forms responder URL, or null if the
 * configuration is missing or is not a safe responder URL.
 * Editor ("/edit") and non-Google URLs are rejected.
 */
export function getNavigatorInterestFormUrl(raw?: string): string | null {
  const value = (raw ?? process.env.NEXT_PUBLIC_NAVIGATOR_INTEREST_FORM_URL ?? '').trim();
  if (!value) return null;

  try {
    const url = new URL(value);
    const isResponder =
      url.protocol === 'https:' &&
      ((url.hostname === 'docs.google.com' &&
        url.pathname.startsWith('/forms/') &&
        !url.pathname.endsWith('/edit')) ||
        url.hostname === 'forms.gle');
    return isResponder ? url.toString() : null;
  } catch {
    return null;
  }
}

/**
 * "Coming soon" teaser for DSB Navigator. Not a purchase or enrollment flow:
 * the CTA opens an externally hosted Google Form to gauge interest.
 */
export function NavigatorTeaser() {
  const formUrl = getNavigatorInterestFormUrl();

  if (!formUrl && typeof window !== 'undefined') {
    console.warn(
      'NEXT_PUBLIC_NAVIGATOR_INTEREST_FORM_URL is not set or is not a valid Google Forms responder URL. The Navigator CTA is hidden.'
    );
  }

  return (
    <section
      aria-labelledby="navigator-teaser-heading"
      className="px-4 sm:px-6 py-12 sm:py-16 bg-white dark:bg-gray-950"
    >
      <div className="max-w-6xl mx-auto">
        <div className="bg-gray-900 rounded-2xl border border-primary-400 px-6 sm:px-10 md:px-14 py-10 sm:py-12 relative overflow-hidden">
          <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-8 md:gap-12 items-center">
            <div className="space-y-4">
              <p className="text-xs sm:text-sm font-semibold tracking-widest uppercase text-primary-400">
                Coming Soon · DSB Navigator
              </p>
              <h2
                id="navigator-teaser-heading"
                className="text-2xl sm:text-3xl md:text-4xl font-bold text-white"
              >
                Your next move deserves a blueprint.
              </h2>
              <p className="text-base text-gray-300 leading-relaxed max-w-xl">
                Personalized engineering and career mentorship, built around your goals.
              </p>

              <div className="pt-2 space-y-3">
                {formUrl && (
                  <a
                    href={formUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center px-6 py-3 text-base font-semibold rounded-lg border-2 border-primary-400 text-primary-400 hover:bg-primary-400 hover:text-gray-900 transition-colors focus:outline-hidden focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 focus:ring-offset-gray-900 min-h-[44px]"
                  >
                    Join the Interest List
                    <span className="sr-only"> (opens in a new tab)</span>
                  </a>
                )}
                <p className="text-sm text-gray-400">
                  Limited founding cohort. Applications not yet open.
                </p>
              </div>
            </div>

            {/* Navigator emblem (decorative) */}
            <div className="hidden md:flex justify-center">
              <img
                src="/images/dsb-navigator.png"
                alt=""
                className="w-40 lg:w-52 h-auto"
                width={1254}
                height={1254}
                loading="lazy"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
