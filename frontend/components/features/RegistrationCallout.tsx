'use client';

import { REGISTRATION_CALLOUT_FEATURES } from '@/lib/data/homepage';

interface RegistrationCalloutProps {
  onCreateAccount: () => void;
}

/**
 * Highlighted registration callout section.
 * Explains what becomes available after creating a free account.
 * Two-column layout: copy + feature list on left, illustration on right.
 */
export function RegistrationCallout({ onCreateAccount }: RegistrationCalloutProps) {
  return (
    <section className="px-4 sm:px-6 py-12 sm:py-16 md:py-20">
      <div className="max-w-6xl mx-auto">
        <div className="bg-gray-900 dark:bg-gray-800 rounded-2xl px-6 sm:px-10 md:px-14 py-10 sm:py-14 md:py-16 relative overflow-hidden">
          {/* Subtle background accent */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary-400/5 rounded-full -translate-y-1/2 translate-x-1/2 pointer-events-none" aria-hidden="true" />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-14 items-center relative">
            {/* Left — copy and CTA */}
            <div className="space-y-6">
              {/* Shield icon */}
              <div className="flex items-center gap-2">
                <svg className="w-6 h-6 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>

              <h2 className="text-2xl sm:text-3xl font-bold text-white">
                Go Beyond the Public Curriculum
              </h2>

              <p className="text-gray-300 text-base leading-relaxed">
                Create a free DSB account to enter the platform, explore the available
                membership options, and choose the learning experience that fits your goals.
              </p>

              {/* Feature list */}
              <ul className="space-y-3">
                {REGISTRATION_CALLOUT_FEATURES.map((feature) => (
                  <li key={feature} className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-primary-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
                    </svg>
                    <span className="text-sm text-gray-300 leading-relaxed">{feature}</span>
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <div className="pt-2">
                <button
                  type="button"
                  onClick={onCreateAccount}
                  className="inline-flex items-center justify-center px-6 py-3 text-base font-semibold rounded-lg bg-primary-400 text-gray-900 hover:bg-primary-500 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 focus:ring-offset-gray-900 min-h-[44px]"
                >
                  Create Your Account
                </button>
              </div>
            </div>

            {/* Right — illustration */}
            <div className="hidden lg:flex justify-center">
              <img
                src="/images/callout-illustration.png"
                alt=""
                className="w-full max-w-[320px] lg:max-w-[380px] h-auto opacity-90"
                width={560}
                height={480}
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}


