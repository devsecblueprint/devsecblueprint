'use client';

interface HeroSectionProps {
  onCreateAccount: () => void;
}

/**
 * Hero section with two-column layout on desktop:
 * Left: eyebrow, headline, supporting copy, CTAs
 * Right: technical DSB illustration
 * Stacks on mobile.
 */
export function HeroSection({ onCreateAccount }: HeroSectionProps) {
  return (
    <section className="px-4 sm:px-6 pt-28 sm:pt-32 pb-16 sm:pb-20 md:pb-24 bg-white dark:bg-gray-950">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-16 items-center">
          {/* Left column — copy and CTAs */}
          <div className="space-y-6">
            {/* Eyebrow */}
            <p className="text-sm font-semibold tracking-widest uppercase text-primary-500 dark:text-primary-400">
              Master DevSecOps &amp; Cloud Security
            </p>

            {/* Heading */}
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-gray-900 dark:text-gray-100 leading-tight">
              Build Practical DevSecOps and Cloud Security Skills
            </h1>

            {/* Supporting copy */}
            <p className="text-lg text-gray-600 dark:text-gray-400 leading-relaxed max-w-xl">
              Structured education, real systems, guided projects, and a community of
              practitioners building security through implementation—not theory alone.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-4 pt-2">
              <a
                href="/curriculum"
                className="inline-flex items-center justify-center px-6 py-3 text-base font-semibold rounded-lg bg-primary-400 text-gray-900 hover:bg-primary-500 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-950 min-h-[44px]"
              >
                Explore the Curriculum
              </a>
              <button
                type="button"
                onClick={onCreateAccount}
                className="inline-flex items-center justify-center px-6 py-3 text-base font-semibold rounded-lg bg-transparent text-gray-900 dark:text-gray-100 border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400 dark:focus:ring-gray-600 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-950 min-h-[44px]"
              >
                Create a Free Account
              </button>
            </div>
          </div>

          {/* Right column — technical illustration */}
          <div className="flex justify-center lg:justify-end">
            <img
              src="/images/hero-illustration.png"
              alt="Technical illustration representing cloud security and DevSecOps infrastructure"
              className="w-full max-w-[360px] sm:max-w-[420px] lg:max-w-[500px] xl:max-w-[560px] h-auto"
              width={800}
              height={640}
            />
          </div>
        </div>
      </div>
    </section>
  );
}


