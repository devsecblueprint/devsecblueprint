'use client';

export type ReviewStatus =
  | 'PENDING_SUBMISSION'
  | 'PENDING_REVIEW'
  | 'REVISIONS_REQUIRED'
  | 'PASSED'
  | 'FAILED';

export interface ReviewSessionStatusProps {
  status: ReviewStatus;
  pathway_id: string;
}

const STATUS_CONFIG: Record<
  ReviewStatus,
  { label: string; hint: string; color: string; icon: string }
> = {
  PENDING_SUBMISSION: {
    label: 'Pending Submission',
    hint: 'Submit your capstone to begin',
    color: 'text-gray-600 dark:text-gray-400',
    icon: '📋',
  },
  PENDING_REVIEW: {
    label: 'Pending Review',
    hint: 'Awaiting review — expect contact within 24-48 hours',
    color: 'text-yellow-600 dark:text-yellow-400',
    icon: '⏳',
  },
  REVISIONS_REQUIRED: {
    label: 'Revisions Required',
    hint: 'Revisions needed — submit updated capstone',
    color: 'text-orange-600 dark:text-orange-400',
    icon: '✏️',
  },
  PASSED: {
    label: 'Passed',
    hint: 'Review passed!',
    color: 'text-green-600 dark:text-green-400',
    icon: '✅',
  },
  FAILED: {
    label: 'Failed',
    hint: 'Review not passed',
    color: 'text-red-600 dark:text-red-400',
    icon: '❌',
  },
};

export function ReviewSessionStatus({
  status,
  pathway_id,
}: ReviewSessionStatusProps) {
  const config = STATUS_CONFIG[status];

  return (
    <div
      className="flex items-start gap-3 rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900"
      role="status"
      aria-label={`Review session status for pathway ${pathway_id}: ${config.label}`}
    >
      <span className="text-2xl" aria-hidden="true">
        {config.icon}
      </span>
      <div className="flex flex-col gap-1">
        <span className={`text-sm font-semibold ${config.color}`}>
          {config.label}
        </span>
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {config.hint}
        </span>
      </div>
    </div>
  );
}
