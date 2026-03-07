/**
 * Page Navigation Component
 * 
 * Provides Previous/Next navigation buttons at the bottom of learning pages.
 * Shows "End Course" button on the last page to return to dashboard.
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export interface PageNavigationProps {
  previousPage?: {
    title: string;
    slug: string;
  };
  nextPage?: {
    title: string;
    slug: string;
  };
}

export function PageNavigation({ previousPage, nextPage }: PageNavigationProps) {
  const router = useRouter();

  const handleEndCourse = () => {
    // Mark current page as complete when ending course
    if (typeof window !== 'undefined' && (window as any).__markPageComplete) {
      (window as any).__markPageComplete();
    }
    // Redirect to dashboard after a brief delay to allow progress to save
    setTimeout(() => {
      router.push('/dashboard');
    }, 300);
  };

  if (!previousPage && !nextPage) {
    return null;
  }

  return (
    <nav 
      className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-800"
      aria-label="Page navigation"
    >
      <div className="flex items-center justify-between gap-4">
        {/* Previous Button */}
        {previousPage ? (
          <Link
            href={previousPage.slug}
            className="flex items-center space-x-2 px-6 py-3 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 min-h-[44px]"
          >
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
                d="M15 19l-7-7 7-7" 
              />
            </svg>
            <div className="text-left">
              <div className="text-xs text-gray-600 dark:text-gray-400">Previous</div>
              <div className="text-sm font-medium">{previousPage.title}</div>
            </div>
          </Link>
        ) : (
          <div /> // Spacer for flex layout
        )}

        {/* Next Button or End Course Button */}
        {nextPage ? (
          <Link
            href={nextPage.slug}
            onClick={() => {
              // Mark current page as complete when clicking Next
              if (typeof window !== 'undefined' && (window as any).__markPageComplete) {
                (window as any).__markPageComplete();
              }
            }}
            className="flex items-center space-x-2 px-6 py-3 bg-amber-500 dark:bg-amber-400 text-gray-900 rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 min-h-[44px] ml-auto"
          >
            <div className="text-right">
              <div className="text-xs text-gray-900 opacity-75">Next</div>
              <div className="text-sm font-medium">{nextPage.title}</div>
            </div>
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
                d="M9 5l7 7-7 7" 
              />
            </svg>
          </Link>
        ) : (
          <button
            onClick={handleEndCourse}
            className="flex items-center space-x-2 px-6 py-3 bg-green-500 dark:bg-green-600 text-white rounded-lg hover:bg-green-600 dark:hover:bg-green-700 transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 min-h-[44px] ml-auto"
          >
            <div className="text-right">
              <div className="text-xs text-white opacity-90">Finished</div>
              <div className="text-sm font-medium">End Course</div>
            </div>
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
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" 
              />
            </svg>
          </button>
        )}
      </div>
    </nav>
  );
}
