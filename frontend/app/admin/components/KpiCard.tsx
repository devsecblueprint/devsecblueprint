'use client';

import React from 'react';
import { Skeleton } from '@/components/ui/Skeleton';
import type { KpiCardProps } from './types';

/**
 * KpiCard displays a single metric with DSB_Gold accent for the value,
 * a label, optional sublabel, optional click handler, and loading skeleton state.
 *
 * When clickable, the card meets WCAG touch-target requirements (44x44px minimum)
 * and supports keyboard activation via Enter/Space.
 */
export function KpiCard({
  label,
  value,
  sublabel,
  onClick,
  isLoading = false,
}: KpiCardProps) {
  const isClickable = Boolean(onClick);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (onClick && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      onClick();
    }
  };

  if (isLoading) {
    return (
      <div
        className="rounded-lg bg-gray-50 dark:bg-gray-800 p-4"
        aria-busy="true"
        aria-label={`Loading ${label}`}
      >
        <Skeleton className="h-8 w-20 mb-2" />
        <Skeleton className="h-4 w-28 mb-1" />
        <Skeleton className="h-3 w-24" />
      </div>
    );
  }

  const cardClasses = [
    'rounded-lg bg-gray-50 dark:bg-gray-800 p-4',
    isClickable &&
      'hover:ring-2 hover:ring-amber-500/50 transition-all cursor-pointer min-h-[44px] min-w-[44px]',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div
      className={cardClasses}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onClick={onClick}
      onKeyDown={isClickable ? handleKeyDown : undefined}
      aria-label={
        isClickable ? `${label}: ${value}. Click for details.` : undefined
      }
    >
      <p className="text-2xl font-bold text-amber-500 dark:text-amber-400">
        {value}
      </p>
      <p className="text-sm text-gray-700 dark:text-gray-300 truncate max-w-[40ch]">
        {label}
      </p>
      {sublabel && (
        <p className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[60ch]">
          {sublabel}
        </p>
      )}
    </div>
  );
}
