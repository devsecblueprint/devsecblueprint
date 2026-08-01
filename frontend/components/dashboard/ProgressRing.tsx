'use client';

interface ProgressRingProps {
  percentage: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
}

export function ProgressRing({
  percentage,
  size = 80,
  strokeWidth = 8,
  className,
}: ProgressRingProps) {
  // Clamp percentage to [0, 100]
  const clampedPercentage = Math.min(100, Math.max(0, Number.isFinite(percentage) ? percentage : 0));

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (clampedPercentage / 100) * circumference;

  return (
    <div
      className={`relative inline-flex items-center justify-center ${className ?? ''}`}
      role="progressbar"
      aria-valuenow={clampedPercentage}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`${Math.round(clampedPercentage)}% complete`}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="transform -rotate-90"
      >
        {/* Track circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          className="stroke-gray-200 dark:stroke-gray-800"
        />
        {/* Progress arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="stroke-amber-500 dark:stroke-amber-400 transition-[stroke-dashoffset] duration-300"
        />
      </svg>
      {/* Visible text label showing the numeric percentage */}
      <span
        className="absolute inset-0 flex items-center justify-center text-sm font-semibold text-gray-900 dark:text-gray-100"
        aria-hidden="true"
      >
        {Math.round(clampedPercentage)}%
      </span>
    </div>
  );
}
