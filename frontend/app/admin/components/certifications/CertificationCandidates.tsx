'use client';

import { useEffect, useState, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { Spinner } from '@/components/ui/Spinner';
import { Button } from '@/components/ui/Button';
import { formatDistanceToNow } from 'date-fns';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type CandidateStatus =
  | 'IN_PROGRESS'
  | 'ELIGIBLE_FOR_AWARD'
  | 'AWARDED'
  | 'EXPIRED'
  | 'REVOKED';

type ReviewSessionStatus =
  | 'PENDING_SUBMISSION'
  | 'PENDING_REVIEW'
  | 'REVISIONS_REQUIRED'
  | 'PASSED'
  | 'FAILED';

interface CandidateListItem {
  user_id: string;
  display_name: string;
  pathway_id: string;
  pathway_display_name: string;
  candidate_status: CandidateStatus;
  review_session_status: ReviewSessionStatus;
  updated_at: string;
}

interface CandidatesResponse {
  candidates: CandidateListItem[];
  page: number;
  limit: number;
  has_more: boolean;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PAGE_SIZE = 20;

const PATHWAY_OPTIONS = [
  { value: '', label: 'All Pathways' },
  { value: 'devsecops-engineering', label: 'DevSecOps Engineering' },
  { value: 'cloud-security-engineering', label: 'Cloud Security Engineering' },
  { value: 'security-engineering-completionist', label: 'Completionist' },
];

const STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'IN_PROGRESS', label: 'In Progress' },
  { value: 'ELIGIBLE_FOR_AWARD', label: 'Eligible for Award' },
  { value: 'AWARDED', label: 'Awarded' },
  { value: 'EXPIRED', label: 'Expired' },
  { value: 'REVOKED', label: 'Revoked' },
];

// ---------------------------------------------------------------------------
// Status badge styling
// ---------------------------------------------------------------------------

const CANDIDATE_STATUS_STYLES: Record<CandidateStatus, string> = {
  IN_PROGRESS:
    'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  ELIGIBLE_FOR_AWARD:
    'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  AWARDED:
    'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  EXPIRED:
    'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400',
  REVOKED:
    'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
};

const REVIEW_STATUS_STYLES: Record<ReviewSessionStatus, string> = {
  PENDING_SUBMISSION:
    'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
  PENDING_REVIEW:
    'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  REVISIONS_REQUIRED:
    'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
  PASSED:
    'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  FAILED:
    'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
};

function formatStatus(status: string): string {
  return status
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatRelativeTime(dateStr: string): string {
  try {
    return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
  } catch {
    return 'N/A';
  }
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface CertificationCandidatesProps {
  onSelectCandidate: (userId: string, pathwayId: string) => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function CertificationCandidates({
  onSelectCandidate,
}: CertificationCandidatesProps) {
  // State
  const [candidates, setCandidates] = useState<CandidateListItem[]>([]);
  const [pathwayFilter, setPathwayFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch candidates
  const fetchCandidates = useCallback(
    async (currentPage: number, pathway: string, status: string) => {
      setIsLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (pathway) params.set('pathway', pathway);
        if (status) params.set('status', status);
        params.set('page', String(currentPage));
        params.set('limit', String(PAGE_SIZE));

        const { data, error: apiError } =
          await apiClient.get<CandidatesResponse>(
            `/admin/certifications/candidates?${params.toString()}`
          );

        if (apiError) {
          setError(apiError);
          return;
        }
        if (data) {
          setCandidates(data.candidates);
          setHasMore(data.has_more);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : 'Failed to fetch candidates'
        );
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  // Fetch on mount and filter/page changes
  useEffect(() => {
    fetchCandidates(page, pathwayFilter, statusFilter);
  }, [page, pathwayFilter, statusFilter, fetchCandidates]);

  // Reset page when filters change
  const handlePathwayChange = (value: string) => {
    setPathwayFilter(value);
    setPage(1);
  };

  const handleStatusChange = (value: string) => {
    setStatusFilter(value);
    setPage(1);
  };

  const handlePrev = () => {
    if (page > 1) setPage(page - 1);
  };

  const handleNext = () => {
    if (hasMore) setPage(page + 1);
  };

  // -------------------------------------------------------------------------
  // Loading state (initial load only)
  // -------------------------------------------------------------------------
  if (isLoading && candidates.length === 0) {
    return (
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Certification Candidates
        </h3>
        {/* Skeleton rows */}
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="h-12 rounded-lg bg-gray-100 dark:bg-gray-800 animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Error state
  // -------------------------------------------------------------------------
  if (error) {
    return (
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Certification Candidates
        </h3>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
          <div className="flex items-start space-x-3">
            <svg
              className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-red-900 dark:text-red-100 mb-1">
                Failed to Load Candidates
              </h4>
              <p className="text-sm text-red-800 dark:text-red-200 mb-3">
                {error}
              </p>
              <button
                onClick={() => fetchCandidates(page, pathwayFilter, statusFilter)}
                className="text-sm font-medium text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  return (
    <div>
      {/* Header */}
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        Certification Candidates
      </h3>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <select
          value={pathwayFilter}
          onChange={(e) => handlePathwayChange(e.target.value)}
          aria-label="Filter by pathway"
          className="px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400"
        >
          {PATHWAY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        <select
          value={statusFilter}
          onChange={(e) => handleStatusChange(e.target.value)}
          aria-label="Filter by candidate status"
          className="px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        {isLoading && (
          <div className="flex items-center">
            <Spinner size="sm" />
          </div>
        )}
      </div>

      {/* Empty state */}
      {candidates.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <svg
            className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p className="text-gray-600 dark:text-gray-400">
            No certification candidates found
          </p>
          {(pathwayFilter || statusFilter) && (
            <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
              Try adjusting your filters
            </p>
          )}
        </div>
      )}

      {/* Desktop table view */}
      {candidates.length > 0 && (
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-800">
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  User
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Pathway
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Candidate Status
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Review Session
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Last Updated
                </th>
              </tr>
            </thead>
            <tbody>
              {candidates.map((candidate) => (
                <tr
                  key={`${candidate.user_id}-${candidate.pathway_id}`}
                  onClick={() =>
                    onSelectCandidate(candidate.user_id, candidate.pathway_id)
                  }
                  className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer"
                  role="button"
                  tabIndex={0}
                  aria-label={`View details for ${candidate.display_name} — ${candidate.pathway_display_name}`}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onSelectCandidate(
                        candidate.user_id,
                        candidate.pathway_id
                      );
                    }
                  }}
                >
                  <td className="py-3 px-4">
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {candidate.display_name}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {candidate.pathway_display_name}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        CANDIDATE_STATUS_STYLES[candidate.candidate_status]
                      }`}
                    >
                      {formatStatus(candidate.candidate_status)}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        REVIEW_STATUS_STYLES[candidate.review_session_status]
                      }`}
                    >
                      {formatStatus(candidate.review_session_status)}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {formatRelativeTime(candidate.updated_at)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Mobile card view */}
      {candidates.length > 0 && (
        <div className="md:hidden space-y-3">
          {candidates.map((candidate) => (
            <div
              key={`${candidate.user_id}-${candidate.pathway_id}-mobile`}
              onClick={() =>
                onSelectCandidate(candidate.user_id, candidate.pathway_id)
              }
              className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 cursor-pointer hover:ring-2 hover:ring-amber-500/50 transition-all"
              role="button"
              tabIndex={0}
              aria-label={`View details for ${candidate.display_name} — ${candidate.pathway_display_name}`}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSelectCandidate(candidate.user_id, candidate.pathway_id);
                }
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {candidate.display_name}
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-500">
                  {formatRelativeTime(candidate.updated_at)}
                </span>
              </div>
              <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                {candidate.pathway_display_name}
              </div>
              <div className="flex flex-wrap gap-2">
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                    CANDIDATE_STATUS_STYLES[candidate.candidate_status]
                  }`}
                >
                  {formatStatus(candidate.candidate_status)}
                </span>
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                    REVIEW_STATUS_STYLES[candidate.review_session_status]
                  }`}
                >
                  {formatStatus(candidate.review_session_status)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination controls */}
      {candidates.length > 0 && (
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <Button
            variant="ghost"
            size="sm"
            onClick={handlePrev}
            disabled={page <= 1}
          >
            Previous
          </Button>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Page {page}
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleNext}
            disabled={!hasMore}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
