/**
 * Restricted Access Component
 *
 * Displayed when a user lacks the VIDEO_RECORDINGS entitlement.
 * Shows a lock icon, explanation message, and link to pricing page.
 *
 * Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.7
 */

'use client';

import Link from 'next/link';

export function RestrictedAccess() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center max-w-md mx-auto px-4">
        {/* Lock icon */}
        <div className="mb-6">
          <svg
            className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
        </div>

        {/* Heading */}
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-3">
          Video Access Restricted
        </h2>

        {/* Explanation */}
        <p className="text-gray-600 dark:text-gray-400 mb-8 leading-relaxed">
          Builder Session Videos are available exclusively to active Builder
          tier members. Upgrade your membership to access recorded sessions,
          track your progress, and learn at your own pace.
        </p>

        {/* CTA Button */}
        <Link
          href="/pricing"
          className="inline-flex items-center px-6 py-3 bg-yellow-500 hover:bg-yellow-600 text-gray-900 font-semibold rounded-lg transition-colors duration-200 shadow-sm"
        >
          View Membership Options
        </Link>
      </div>
    </div>
  );
}
