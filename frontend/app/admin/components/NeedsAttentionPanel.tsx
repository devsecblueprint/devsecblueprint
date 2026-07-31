'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { useAdminContext } from './AdminDashboardProvider';
import type { AttentionItem } from './types';

/**
 * NeedsAttentionPanel displays actionable counts for items requiring admin review.
 *
 * - Consumes `attentionCounts` from the AdminDashboard context
 * - Renders each item with a Badge when count > 0
 * - On click, scrolls to the corresponding Accordion section
 * - Shows skeleton loading state while data loads
 * - Shows error state with retry on failure/timeout
 * - Shows "No items require attention" when all counts are zero
 */
export function NeedsAttentionPanel() {
  const { attentionCounts, isLoading, errors, refetchAll } = useAdminContext();

  // Map context attention counts to AttentionItem array
  const attentionItems: AttentionItem[] = [
    {
      id: 'pending-capstones',
      label: 'Pending Capstone Submissions',
      count: attentionCounts.pendingCapstones,
      targetSectionId: 'reviews',
    },
    {
      id: 'pending-testimonials',
      label: 'Pending Testimonials',
      count: attentionCounts.pendingTestimonials,
      targetSectionId: 'reviews',
    },
    {
      id: 'module-health-issues',
      label: 'Module Health Issues',
      count: attentionCounts.moduleHealthIssues,
      targetSectionId: 'learning-content',
    },
    {
      id: 'registry-issues',
      label: 'Registry Validation Issues',
      count: attentionCounts.registryIssues,
      targetSectionId: 'learning-content',
    },
  ];

  const hasError =
    errors.submissions !== null ||
    errors.moduleHealth !== null ||
    errors.registryStatus !== null;

  const allZero = attentionItems.every((item) => item.count === 0);

  const handleItemClick = (targetSectionId: string) => {
    document
      .getElementById(targetSectionId)
      ?.scrollIntoView({ behavior: 'smooth' });
  };

  // Loading state
  if (isLoading) {
    return (
      <Card className="h-full">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Needs Attention
        </h2>
        <div className="space-y-3" aria-busy="true" aria-label="Loading attention items">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between">
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-6 w-8 rounded-full" />
            </div>
          ))}
        </div>
      </Card>
    );
  }

  // Error state
  if (hasError) {
    return (
      <Card className="h-full">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Needs Attention
        </h2>
        <div className="flex flex-col items-center justify-center py-6 text-center">
          <svg
            className="w-8 h-8 text-red-500 mb-2"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z"
            />
          </svg>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
            Failed to load attention data
          </p>
          <button
            onClick={refetchAll}
            className="px-3 py-1.5 text-sm font-medium rounded-md bg-amber-500 text-white hover:bg-amber-600 transition-colors min-h-[44px] min-w-[44px]"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  // All clear state
  if (allZero) {
    return (
      <Card className="h-full">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Needs Attention
        </h2>
        <div className="flex flex-col items-center justify-center py-6 text-center">
          <svg
            className="w-8 h-8 text-green-500 mb-2"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
            />
          </svg>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            No items require attention
          </p>
        </div>
      </Card>
    );
  }

  // Normal state with attention items
  return (
    <Card className="h-full">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        Needs Attention
      </h2>
      <ul className="space-y-2" role="list">
        {attentionItems.map((item) => (
          <li key={item.id}>
            <button
              onClick={() => handleItemClick(item.targetSectionId)}
              className="w-full flex items-center justify-between rounded-lg px-3 py-2 text-left transition-colors hover:bg-gray-100 dark:hover:bg-gray-800 min-h-[44px]"
              aria-label={`${item.label}: ${item.count}. Click to navigate to section.`}
            >
              <span className="text-sm text-gray-700 dark:text-gray-300">
                {item.label}
              </span>
              {item.count > 0 ? (
                <Badge variant="warning" size="sm">
                  {item.count}
                </Badge>
              ) : (
                <span className="text-xs text-gray-400 dark:text-gray-500">
                  0
                </span>
              )}
            </button>
          </li>
        ))}
      </ul>
    </Card>
  );
}
