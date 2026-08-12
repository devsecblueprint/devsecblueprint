'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { format } from 'date-fns';
import { ReviewOutcomeForm } from './ReviewOutcomeForm';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type CandidateStatus =
  | 'NOT_STARTED'
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

type CredentialStatus = 'ACTIVE' | 'RENEWAL_ELIGIBLE' | 'EXPIRED' | 'REVOKED';

interface ReviewGateState {
  status: ReviewSessionStatus;
  reviewed_at: string | null;
  reviewer_id: string | null;
}

interface CandidateRecord {
  pathway_id: string;
  pathway_version?: string;
  candidate_status: CandidateStatus;
  review_gate: ReviewGateState;
  started_at: string;
  updated_at: string;
  credential_id: string | null;
  prior_credential_id: string | null;
  display_name?: string;
}

interface ReviewHistoryItem {
  revision_number: number;
  status: ReviewSessionStatus;
  submission_url: string;
  rubric_scores?: Record<string, unknown>;
  evaluation_dimensions?: Record<string, string>;
  reviewer_notes?: string;
  reviewer_id?: string;
  submitted_at: string;
  reviewed_at: string | null;
}

interface CredentialRecord {
  credential_id: string;
  pathway_id: string;
  credential_status: CredentialStatus;
  issued_at: string;
  expires_at: string;
  is_grandfathered?: boolean;
  is_recertification?: boolean;
}

interface CandidateDetailResponse {
  candidate: CandidateRecord;
  review_history: ReviewHistoryItem[];
  credential: CredentialRecord | null;
}

// ---------------------------------------------------------------------------
// Status styling
// ---------------------------------------------------------------------------

const CANDIDATE_STATUS_STYLES: Record<CandidateStatus, string> = {
  NOT_STARTED:
    'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
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

const CREDENTIAL_STATUS_STYLES: Record<CredentialStatus, string> = {
  ACTIVE:
    'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  RENEWAL_ELIGIBLE:
    'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  EXPIRED:
    'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400',
  REVOKED:
    'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
};

const PATHWAY_DISPLAY_NAMES: Record<string, string> = {
  'devsecops-engineering': 'DevSecOps Engineering',
  'cloud-security-engineering': 'Cloud Security Engineering',
  'security-engineering-completionist': 'Security Engineering Completionist',
};

function formatStatus(status: string): string {
  return status
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'N/A';
  try {
    return format(new Date(dateStr), 'MMM d, yyyy');
  } catch {
    return 'N/A';
  }
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface CandidateDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  userId: string;
  pathwayId: string;
  onActionComplete: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function CandidateDetailModal({
  isOpen,
  onClose,
  userId,
  pathwayId,
  onActionComplete,
}: CandidateDetailModalProps) {
  const [data, setData] = useState<CandidateDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [isGranting, setIsGranting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Animate in
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => setIsVisible(true), 10);
    } else {
      setIsVisible(false);
    }
  }, [isOpen]);

  // Focus management
  useEffect(() => {
    if (!isOpen) return;
    previousFocusRef.current = document.activeElement as HTMLElement;
    const closeBtn = modalRef.current?.querySelector<HTMLElement>('button');
    closeBtn?.focus();
    return () => {
      previousFocusRef.current?.focus();
    };
  }, [isOpen]);

  // Prevent body scroll
  useEffect(() => {
    if (!isOpen) return;
    const original = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = original;
    };
  }, [isOpen]);

  // Keyboard handling
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (showReviewForm) {
          setShowReviewForm(false);
        } else {
          onClose();
        }
        return;
      }
      if (e.key !== 'Tab') return;
      const modal = modalRef.current;
      if (!modal) return;
      const focusable = modal.querySelectorAll<HTMLElement>(
        'button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [href], [tabindex]:not([tabindex="-1"])'
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    },
    [onClose, showReviewForm]
  );

  useEffect(() => {
    if (!isOpen) return;
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, handleKeyDown]);

  // Fetch candidate detail
  const fetchDetail = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data: responseData, error: apiError } =
        await apiClient.get<CandidateDetailResponse>(
          `/admin/certifications/candidates/${encodeURIComponent(userId)}/${encodeURIComponent(pathwayId)}`
        );
      if (apiError) {
        setError(apiError);
        return;
      }
      if (responseData) {
        setData(responseData);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to fetch candidate detail'
      );
    } finally {
      setIsLoading(false);
    }
  }, [userId, pathwayId]);

  useEffect(() => {
    if (isOpen) {
      fetchDetail();
      setShowReviewForm(false);
      setActionError(null);
      setActionSuccess(null);
    }
  }, [isOpen, fetchDetail]);

  // Grant credential action
  const handleGrantCredential = async () => {
    setIsGranting(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      const { data: grantData, error: apiError } = await apiClient.post<{
        status: string;
        credential_id: string;
      }>(
        `/admin/certifications/candidates/${encodeURIComponent(userId)}/${encodeURIComponent(pathwayId)}/grant`,
        {}
      );
      if (apiError) {
        setActionError(apiError);
        return;
      }
      if (grantData) {
        setActionSuccess(
          `Credential granted successfully: ${grantData.credential_id}`
        );
        fetchDetail();
        onActionComplete();
      }
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : 'Failed to grant credential'
      );
    } finally {
      setIsGranting(false);
    }
  };

  // Review outcome complete callback
  const handleReviewComplete = () => {
    setShowReviewForm(false);
    setActionSuccess('Review outcome recorded successfully');
    fetchDetail();
    onActionComplete();
  };

  if (!isOpen) return null;

  const pathwayDisplayName =
    PATHWAY_DISPLAY_NAMES[pathwayId] || pathwayId;

  const candidate = data?.candidate;
  const reviewHistory = data?.review_history || [];
  const credential = data?.credential;

  const isAwarded = candidate?.candidate_status === 'AWARDED';
  const isPendingReview =
    candidate?.review_gate?.status === 'PENDING_REVIEW';

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-opacity duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
      role="dialog"
      aria-modal="true"
      aria-labelledby="candidate-detail-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        ref={modalRef}
        className={`relative w-full max-w-3xl max-h-[90vh] flex flex-col transform transition-all duration-300 ${
          isVisible ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        }`}
      >
        <Card padding="lg">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2
              id="candidate-detail-title"
              className="text-xl font-semibold text-gray-900 dark:text-gray-100"
            >
              Candidate Detail
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              aria-label="Close modal"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="overflow-y-auto max-h-[70vh]">
            {isLoading ? (
              <div className="flex items-center justify-center min-h-[200px]">
                <Spinner size="lg" />
              </div>
            ) : error ? (
              <div className="text-center py-8">
                <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
                <Button variant="ghost" onClick={fetchDetail}>
                  Retry
                </Button>
              </div>
            ) : data && candidate ? (
              <div className="space-y-6">
                {/* Show review form if toggled */}
                {showReviewForm ? (
                  <ReviewOutcomeForm
                    userId={userId}
                    pathwayId={pathwayId}
                    onComplete={handleReviewComplete}
                    onCancel={() => setShowReviewForm(false)}
                  />
                ) : (
                  <>
                    {/* User info & pathway */}
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                          {candidate.display_name || userId}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {pathwayDisplayName}
                        </p>
                      </div>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          CANDIDATE_STATUS_STYLES[candidate.candidate_status]
                        }`}
                      >
                        {formatStatus(candidate.candidate_status)}
                      </span>
                    </div>

                    {/* Review Session Status */}
                    <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                      <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                        Review Session Status
                      </h4>
                      <div className="flex items-center space-x-3 mb-2">
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          Current Status:
                        </span>
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            REVIEW_STATUS_STYLES[candidate.review_gate.status]
                          }`}
                        >
                          {formatStatus(candidate.review_gate.status)}
                        </span>
                      </div>
                      {reviewHistory.length > 0 && (
                        <div className="mt-2">
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Latest submission:{' '}
                            <a
                              href={reviewHistory[reviewHistory.length - 1]?.submission_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-amber-600 dark:text-amber-400 hover:underline"
                            >
                              {reviewHistory[reviewHistory.length - 1]?.submission_url}
                            </a>
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                            {reviewHistory.length} revision(s) total
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Revision History */}
                    {reviewHistory.length > 0 && (
                      <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                          Revision History
                        </h4>
                        <div className="space-y-3 max-h-48 overflow-y-auto">
                          {reviewHistory.map((review) => (
                            <div
                              key={review.revision_number}
                              className="flex items-start justify-between border-b border-gray-100 dark:border-gray-800 pb-2 last:border-0 last:pb-0"
                            >
                              <div>
                                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                  Revision #{review.revision_number}
                                </span>
                                <p className="text-xs text-gray-500 dark:text-gray-500">
                                  Submitted: {formatDate(review.submitted_at)}
                                  {review.reviewed_at &&
                                    ` | Reviewed: ${formatDate(review.reviewed_at)}`}
                                </p>
                                {review.reviewer_notes && (
                                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 italic">
                                    &ldquo;{review.reviewer_notes.slice(0, 100)}
                                    {review.reviewer_notes.length > 100 ? '...' : ''}&rdquo;
                                  </p>
                                )}
                              </div>
                              <span
                                className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                                  REVIEW_STATUS_STYLES[review.status]
                                }`}
                              >
                                {formatStatus(review.status)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Credential Section */}
                    {credential && (
                      <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                          Credential
                        </h4>
                        <div className="grid grid-cols-2 gap-3 text-sm">
                          <div>
                            <span className="text-gray-500 dark:text-gray-500">
                              Credential ID:
                            </span>
                            <p className="font-mono text-gray-900 dark:text-gray-100">
                              {credential.credential_id}
                            </p>
                          </div>
                          <div>
                            <span className="text-gray-500 dark:text-gray-500">
                              Status:
                            </span>
                            <p>
                              <span
                                className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                                  CREDENTIAL_STATUS_STYLES[credential.credential_status]
                                }`}
                              >
                                {formatStatus(credential.credential_status)}
                              </span>
                            </p>
                          </div>
                          <div>
                            <span className="text-gray-500 dark:text-gray-500">
                              Issued:
                            </span>
                            <p className="text-gray-900 dark:text-gray-100">
                              {formatDate(credential.issued_at)}
                            </p>
                          </div>
                          <div>
                            <span className="text-gray-500 dark:text-gray-500">
                              Expires:
                            </span>
                            <p className="text-gray-900 dark:text-gray-100">
                              {formatDate(credential.expires_at)}
                            </p>
                          </div>
                          {credential.is_grandfathered && (
                            <div className="col-span-2">
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400">
                                Grandfathered
                              </span>
                            </div>
                          )}
                          {credential.is_recertification && (
                            <div className="col-span-2">
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
                                Re-certification
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Action messages */}
                    {actionSuccess && (
                      <div className="rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-3">
                        <p className="text-sm text-green-800 dark:text-green-200">
                          {actionSuccess}
                        </p>
                      </div>
                    )}
                    {actionError && (
                      <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-3">
                        <p className="text-sm text-red-800 dark:text-red-200">
                          {actionError}
                        </p>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                      <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                        Actions
                      </h4>
                      <div className="flex flex-wrap gap-3">
                        {/* Record Review Outcome — visible when PENDING_REVIEW */}
                        {isPendingReview && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => setShowReviewForm(true)}
                          >
                            Record Review Outcome
                          </Button>
                        )}

                        {/* Grant Credential — visible when NOT AWARDED */}
                        {!isAwarded && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={handleGrantCredential}
                            disabled={isGranting}
                          >
                            {isGranting ? 'Granting...' : 'Grant Credential'}
                          </Button>
                        )}

                        {/* Revoke Credential — visible when AWARDED */}
                        {isAwarded && credential && (
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => {
                              // This will be handled by RevokeCredentialModal in task 12.4
                              setActionError(
                                'Revoke functionality available via the Revoke Credential modal (coming soon)'
                              );
                            }}
                          >
                            Revoke Credential
                          </Button>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </div>
            ) : null}
          </div>

          {/* Footer */}
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
            <Button variant="ghost" onClick={onClose}>
              Close
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
