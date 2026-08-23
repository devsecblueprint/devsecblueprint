'use client';

import Link from 'next/link';

export type CandidateStatus =
  | 'NOT_STARTED'
  | 'IN_PROGRESS'
  | 'ELIGIBLE_FOR_AWARD'
  | 'AWARDED'
  | 'EXPIRED'
  | 'REVOKED';

export interface PathwayCardProps {
  pathway_id: string;
  display_name: string;
  description: string;
  candidate_status: CandidateStatus;
}

const STATUS_BADGE_STYLES: Record<CandidateStatus, string> = {
  NOT_STARTED: 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  IN_PROGRESS: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  ELIGIBLE_FOR_AWARD: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  AWARDED: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  EXPIRED: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  REVOKED: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

const STATUS_LABELS: Record<CandidateStatus, string> = {
  NOT_STARTED: 'Not Started',
  IN_PROGRESS: 'In Progress',
  ELIGIBLE_FOR_AWARD: 'Eligible for Award',
  AWARDED: 'Awarded',
  EXPIRED: 'Expired',
  REVOKED: 'Revoked',
};

export function PathwayCard({
  pathway_id,
  display_name,
  description,
  candidate_status,
}: PathwayCardProps) {
  return (
    <Link
      href={`/dashboard/certifications/detail?pathway=${pathway_id}`}
      className="block rounded-2xl border border-gray-200 bg-white p-6 shadow-lg transition-shadow hover:shadow-xl dark:border-gray-800 dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
      aria-label={`${display_name} certification pathway — ${STATUS_LABELS[candidate_status]}`}
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {display_name}
        </h3>
        <span
          className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${STATUS_BADGE_STYLES[candidate_status]}`}
          aria-label={`Status: ${STATUS_LABELS[candidate_status]}`}
        >
          {STATUS_LABELS[candidate_status]}
        </span>
      </div>
      <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
        {description}
      </p>
    </Link>
  );
}
