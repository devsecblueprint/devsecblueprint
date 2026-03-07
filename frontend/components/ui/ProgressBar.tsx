import React from 'react';
import { ProgressBarHeight } from '@/lib/types';

export interface ProgressBarProps {
  percentage: number;
  showLabel?: boolean;
  height?: ProgressBarHeight;
}

export function ProgressBar({
  percentage,
  showLabel = false,
  height = 'md'
}: ProgressBarProps) {
  // Clamp percentage between 0 and 100
  const clampedPercentage = Math.min(Math.max(percentage, 0), 100);

  // Base styles
  const containerStyles = 'w-full bg-gray-800 rounded-full overflow-hidden';

  // Height variants
  const heightStyles: Record<ProgressBarHeight, string> = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4'
  };

  // Fill styles
  const fillStyles = 'bg-amber-500 h-full transition-all duration-300 ease-in-out';

  return (
    <div className="w-full">
      <div className={`${containerStyles} ${heightStyles[height]}`}>
        <div
          className={fillStyles}
          style={{ width: `${clampedPercentage}%` }}
          role="progressbar"
          aria-valuenow={clampedPercentage}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      {showLabel && (
        <div className="mt-2 text-sm text-gray-400 text-right">
          {clampedPercentage}%
        </div>
      )}
    </div>
  );
}
