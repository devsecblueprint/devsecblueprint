'use client';

interface FinalCTAProps {
  onCreateAccount: () => void;
}

/**
 * Final conversion section at the bottom of the homepage.
 * "Ready to Start Building?" with primary and secondary CTAs.
 */
export function FinalCTA({ onCreateAccount }: FinalCTAProps) {
  return (
    <section className="px-4 sm:px-6 py-16 sm:py-20 md:py-24 bg-white dark:bg-gray-950">
      <div className="max-w-3xl mx-auto text-center space-y-6">
        {/* Decorative icon */}
        <div className="flex justify-center" aria-hidden="true">
          <svg className="w-10 h-10 text-primary-500 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.841m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
          </svg>
        </div>

        <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 dark:text-gray-100">
          Ready to Start Building?
        </h2>

        <p className="text-base sm:text-lg text-gray-600 dark:text-gray-400 leading-relaxed max-w-2xl mx-auto">
          Explore the curriculum and begin developing practical DevSecOps and cloud
          security experience through real systems.
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
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
            Join The DevSec Blueprint
          </button>
        </div>
      </div>
    </section>
  );
}
