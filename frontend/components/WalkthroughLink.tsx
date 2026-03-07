'use client';

import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/Badge';
import type { Walkthrough } from '@/lib/types';

export interface WalkthroughLinkProps {
  walkthroughId: string;
}

/**
 * WalkthroughLink Component
 * 
 * Displays a styled card linking to a walkthrough from module content.
 * Used via markdown directive in course modules.
 * 
 * Features:
 * - Loads walkthrough metadata by ID from API
 * - Displays title, description, and difficulty badge
 * - Clickable card navigates to walkthrough detail page
 * - Handles invalid walkthrough IDs with warning message
 * 
 * Requirements: 9.3, 9.4, 9.5, 9.6
 */
export function WalkthroughLink({ walkthroughId }: WalkthroughLinkProps) {
  const [walkthrough, setWalkthrough] = useState<Walkthrough | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function loadWalkthrough() {
      try {
        const response = await fetch(`/api/walkthroughs/${walkthroughId}`);
        if (response.ok) {
          const data = await response.json();
          setWalkthrough(data);
        } else {
          setError(true);
        }
      } catch (err) {
        console.error('Failed to load walkthrough:', err);
        setError(true);
      } finally {
        setIsLoading(false);
      }
    }

    loadWalkthrough();
  }, [walkthroughId]);

  // Loading state
  if (isLoading) {
    return (
      <div className="my-6 p-4 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg animate-pulse">
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
      </div>
    );
  }

  // Handle invalid walkthrough ID or error
  if (error || !walkthrough) {
    return (
      <div 
        className="my-6 p-4 bg-amber-50 dark:bg-amber-900/20 border-l-4 border-amber-500 rounded-r-lg"
        role="alert"
        aria-live="polite"
      >
        <div className="flex items-start">
          <svg 
            className="w-5 h-5 text-amber-500 mr-3 mt-0.5 flex-shrink-0" 
            fill="currentColor" 
            viewBox="0 0 20 20"
            aria-hidden="true"
          >
            <path 
              fillRule="evenodd" 
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" 
              clipRule="evenodd" 
            />
          </svg>
          <div>
            <h3 className="text-sm font-semibold text-amber-800 dark:text-amber-300 mb-1">
              Walkthrough Not Found
            </h3>
            <p className="text-sm text-amber-700 dark:text-amber-400">
              Referenced walkthrough <code className="px-1 py-0.5 bg-amber-100 dark:bg-amber-900/40 rounded text-xs">{walkthroughId}</code> could not be found.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Get difficulty badge variant
  const difficultyVariant = {
    'Beginner': 'success' as const,
    'Intermediate': 'warning' as const,
    'Advanced': 'default' as const,
  }[walkthrough.difficulty];

  return (
    <a
      href={`/walkthroughs/${walkthrough.id}`}
      className="block my-6 group no-underline"
      aria-label={`View walkthrough: ${walkthrough.title}`}
    >
      <div className="bg-gradient-to-br from-primary-50 to-primary-100 dark:from-primary-900/20 dark:to-primary-800/20 border-2 border-primary-200 dark:border-primary-700 rounded-lg p-5 hover:border-primary-400 dark:hover:border-primary-500 transition-all hover:shadow-lg">
        {/* Header with Icon and Badge */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-start flex-1">
            {/* Walkthrough Icon */}
            <div className="flex-shrink-0 w-10 h-10 bg-primary-500 dark:bg-primary-600 rounded-lg flex items-center justify-center mr-3">
              <svg 
                className="w-6 h-6 text-white" 
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
            </div>
            
            {/* Title */}
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors mb-1">
                {walkthrough.title}
              </h2>
              <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
                <span className="inline-flex items-center">
                  <svg 
                    className="w-3.5 h-3.5 mr-1" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" 
                    />
                  </svg>
                  {walkthrough.estimatedTime} minutes
                </span>
              </div>
            </div>
          </div>
          
          {/* Difficulty Badge */}
          <div className="ml-3 flex-shrink-0">
            <Badge variant={difficultyVariant} size="sm">
              {walkthrough.difficulty}
            </Badge>
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-gray-700 dark:text-gray-300 mb-3 line-clamp-2">
          {walkthrough.description}
        </p>

        {/* Topics */}
        {walkthrough.topics.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {walkthrough.topics.slice(0, 4).map((topic) => (
              <span
                key={topic}
                className="px-2 py-1 text-xs bg-white/60 dark:bg-gray-800/60 text-gray-700 dark:text-gray-300 rounded border border-primary-200 dark:border-primary-700"
              >
                {topic}
              </span>
            ))}
            {walkthrough.topics.length > 4 && (
              <span className="px-2 py-1 text-xs text-gray-600 dark:text-gray-400">
                +{walkthrough.topics.length - 4} more
              </span>
            )}
          </div>
        )}

        {/* Call to Action */}
        <div className="flex items-center text-sm font-medium text-primary-600 dark:text-primary-400 group-hover:text-primary-700 dark:group-hover:text-primary-300 transition-colors">
          <span>View Walkthrough</span>
          <svg 
            className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" 
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
        </div>
      </div>
    </a>
  );
}
