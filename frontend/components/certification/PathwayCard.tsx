'use client';

import Link from 'next/link';

/**
 * Candidate status type matching backend CandidateStatus enum.
 */
export type CandidateStatus =
  | 'NOT_STARTED'
  | 'IN_PROGRESS'
  | 'ELIGIBLE_FOR_AWARD'
  | 'AWARDED'
  | 'EXPIRED'
  | 'REVOKED';

/**
 * Pathway data shape returned from GET /certifications
 */
export interface PathwayWithStatus {
  pathway_id: string;
  display_name: string;
  description: string;
  candidate_status: CandidateStatus | null;
  credential_id?: string | null;
  is_completionist?: boolean;
}

/**
 * Status badge color mapping
 */
function getStatusBadge(status: CandidateStatus | null): { label: string; className: string } {
  switch (status) {
    case 'NOT_STARTED':
      return { label: 'Not Started', className: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' };
    case 'IN_PROGRESS':
      return { label: 'In Progress', className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' };
    case 'ELIGIBLE_FOR_AWARD':
      return { label: 'Eligible', className: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300' };
    case 'AWARDED':
      return { label: 'Awarded', className: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' };
    case 'EXPIRED':
      return { label: 'Expired', className: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300' };
    case 'REVOKED':
      return { label: 'Revoked', className: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300' };
    default:
      return { label: 'Not Started', className: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' };
  }
}

interface PathwayCardProps {
  pathway: PathwayWithStatus;
}

/**
 * PathwayCard — Displays a pathway overview with status badge.
 * Links to the pathway detail page.
 */
export function PathwayCard({ pathway }: PathwayCardProps) {
  const badge = getStatusBadge(pathway.candidate_status);

  return (
    <Link
      href={`/dashboard/certifications/${pathway.pathway_id}`}
      className="block bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6 hover:border-primary-300 dark:hover:border-primary-700 hover:shadow-md transition-all"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 truncate">
            {pathway.display_name}
          </h3>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
            {pathway.description}
          </p>
          {pathway.is_completionist && (
            <p className="mt-2 text-xs text-purple-600 dark:text-purple-400 font-medium">
              Auto-calculated from primary pathways
            </p>
          )}
        </div>
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${badge.className}`}>
          {badge.label}
        </span>
      </div>
    </Link>
  );
}
