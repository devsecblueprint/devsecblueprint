/**
 * Spinner Component
 * 
 * A reusable loading spinner with different sizes.
 */

import React from 'react';

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const sizeClasses = {
  sm: 'w-4 h-4 border-2',
  md: 'w-8 h-8 border-2',
  lg: 'w-12 h-12 border-4',
  xl: 'w-16 h-16 border-4',
};

export function Spinner({ size = 'md', className = '' }: SpinnerProps) {
  return (
    <div
      className={`${sizeClasses[size]} border-gray-200 dark:border-gray-800 border-t-primary-500 dark:border-t-primary-400 rounded-full animate-spin ${className}`}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
}

/**
 * Centered Spinner for full-width containers
 */
export function CenteredSpinner({ size = 'lg' }: { size?: 'sm' | 'md' | 'lg' | 'xl' }) {
  return (
    <div className="flex items-center justify-center py-12">
      <Spinner size={size} />
    </div>
  );
}

/**
 * Inline Spinner for text
 */
export function InlineSpinner() {
  return <Spinner size="sm" className="inline-block ml-2" />;
}
