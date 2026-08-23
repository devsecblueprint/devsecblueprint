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
      return { label: 'Not Started', className: 'bg-gray-700/50 text-gray-300 border border-gray-600' };
    case 'IN_PROGRESS':
      return { label: 'In Progress', className: 'bg-blue-900/40 text-blue-300 border border-blue-700' };
    case 'ELIGIBLE_FOR_AWARD':
      return { label: 'Eligible', className: 'bg-yellow-900/40 text-yellow-300 border border-yellow-700' };
    case 'AWARDED':
      return { label: 'Awarded', className: 'bg-green-900/40 text-green-300 border border-green-700' };
    case 'EXPIRED':
      return { label: 'Expired', className: 'bg-orange-900/40 text-orange-300 border border-orange-700' };
    case 'REVOKED':
      return { label: 'Revoked', className: 'bg-red-900/40 text-red-300 border border-red-700' };
    default:
      return { label: 'Not Started', className: 'bg-gray-700/50 text-gray-300 border border-gray-600' };
  }
}

/**
 * Card border color based on status
 */
function getCardBorderClass(status: CandidateStatus | null): string {
  switch (status) {
    case 'AWARDED':
      return 'border-yellow-500/70';
    case 'IN_PROGRESS':
      return 'border-blue-500/50';
    case 'ELIGIBLE_FOR_AWARD':
      return 'border-yellow-600/50';
    default:
      return 'border-gray-800';
  }
}

/**
 * Icon per status
 */
function getStatusIcon(status: CandidateStatus | null): React.ReactNode {
  switch (status) {
    case 'AWARDED':
      return (
        <svg className="w-10 h-10 text-yellow-500/80" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      );
    case 'IN_PROGRESS':
      return (
        <svg className="w-10 h-10 text-blue-500/80" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      );
    default:
      return (
        <svg className="w-10 h-10 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      );
  }
}

interface PathwayCardProps {
  pathway: PathwayWithStatus;
}

/**
 * PathwayCard — Displays a certification pathway as a visual tile.
 * Shows an icon, pathway name, and status badge.
 */
export function PathwayCard({ pathway }: PathwayCardProps) {
  const badge = getStatusBadge(pathway.candidate_status);
  const borderClass = getCardBorderClass(pathway.candidate_status);

  return (
    <Link
      href={`/dashboard/certifications/detail?pathway=${pathway.pathway_id}`}
      className={`group block bg-gray-900 border ${borderClass} rounded-xl p-6 hover:bg-gray-800/70 hover:shadow-xl hover:scale-[1.01] transition-all duration-200`}
    >
      <div className="flex flex-col h-full gap-4">
        {/* Icon + badge row */}
        <div className="flex items-start justify-between">
          {getStatusIcon(pathway.candidate_status)}
          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap ${badge.className}`}>
            {badge.label}
          </span>
        </div>

        {/* Pathway name */}
        <h3 className="text-base font-semibold text-gray-100 group-hover:text-white transition-colors">
          {pathway.display_name}
        </h3>

        {/* Subtle arrow indicator */}
        <div className="mt-auto flex items-center text-xs text-gray-500 group-hover:text-gray-300 transition-colors">
          <span>View details</span>
          <svg className="w-3.5 h-3.5 ml-1 group-hover:translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </Link>
  );
}
