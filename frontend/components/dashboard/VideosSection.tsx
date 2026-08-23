/**
 * Videos Section for the Dashboard
 *
 * Shows a brief preview of recent or in-progress videos with a
 * link to the full videos catalog.
 */

'use client';

import Link from 'next/link';
import { Card } from '@/components/ui/Card';

export function VideosSection() {
  return (
    <section>
      <div className="flex items-center justify-between mb-4 sm:mb-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
          Builder Session Videos
        </h2>
        <Link
          href="/videos"
          className="text-sm font-medium text-primary-500 hover:text-primary-600 dark:text-primary-400 dark:hover:text-primary-300 transition-colors"
        >
          View All &rarr;
        </Link>
      </div>

      <Card>
        <div className="flex items-center gap-4">
          <div className="flex-shrink-0">
            <svg
              className="w-10 h-10 text-yellow-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
          </div>
          <div className="flex-1">
            <p className="text-gray-700 dark:text-gray-300">
              Watch recorded Builder Sessions and track your learning progress.
              Available to Builder tier members.
            </p>
          </div>
          <Link
            href="/videos"
            className="flex-shrink-0 px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-gray-900 text-sm font-semibold rounded-lg transition-colors"
          >
            Browse Videos
          </Link>
        </div>
      </Card>
    </section>
  );
}
