/**
 * Skeleton Component
 * 
 * Loading placeholder components with shimmer animation.
 */

import React from 'react';

export interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-gray-200 dark:bg-gray-800 rounded ${className}`}
      aria-hidden="true"
    />
  );
}

/**
 * Skeleton for stat cards
 */
export function SkeletonStatCard() {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
      <div className="flex flex-col items-center text-center">
        <Skeleton className="w-8 h-8 mb-3 rounded-full" />
        <Skeleton className="w-16 h-10 mb-2" />
        <Skeleton className="w-24 h-4" />
      </div>
    </div>
  );
}

/**
 * Skeleton for badge cards
 */
export function SkeletonBadgeCard() {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
      <div className="flex flex-col items-center text-center">
        <Skeleton className="w-12 h-12 mb-3 rounded-full" />
        <Skeleton className="w-20 h-4 mb-1" />
        <Skeleton className="w-24 h-3 mb-2" />
        <Skeleton className="w-16 h-6 rounded-full" />
      </div>
    </div>
  );
}

/**
 * Skeleton for activity cards
 */
export function SkeletonActivityCard() {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
      <div className="flex items-center space-x-4">
        <Skeleton className="w-10 h-10 rounded-full flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <Skeleton className="w-32 h-4 mb-2" />
          <Skeleton className="w-24 h-3" />
        </div>
        <Skeleton className="w-16 h-3 flex-shrink-0" />
      </div>
    </div>
  );
}

/**
 * Skeleton for learning path cards
 */
export function SkeletonLearningCard() {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <Skeleton className="w-32 h-5 mb-2" />
          <Skeleton className="w-full h-3 mb-3" />
          <Skeleton className="w-20 h-6 rounded-full" />
        </div>
        <Skeleton className="w-10 h-10 rounded-lg ml-4" />
      </div>
    </div>
  );
}
