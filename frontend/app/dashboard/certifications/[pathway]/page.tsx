'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { AuthGuard } from '@/components/AuthGuard';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { apiClient } from '@/lib/api';
import { ReviewSessionStatus } from '@/app/components/certification/ReviewSessionStatus';
import type { ReviewStatus } from '@/app/components/certification/ReviewSessionStatus';
import { CredentialBadge } from '@/app/components/certification/CredentialBadge';
import type { CredentialStatus } from '@/app/components/certification/CredentialBadge';
import { CertificateDownload } from '@/app/components/certification/CertificateDownload';

/**
 * Candidate record returned from GET /certifications/{pathway_id}
 */
interface CandidateRecord {
  pathway_id: string;
  pathway_version: string;
  candidate_status: string;
  review_gate: {
    status: ReviewStatus;
    reviewed_at: string | null;
    reviewer_id: string | null;
  };
  started_at: string;
  updated_at: string;
  credential_id: string | null;
  prior_credential_id: string | null;
}

/**
 * Credential record returned from GET /certifications/{pathway_id}/credential
 */
interface CredentialRecord {
  credential_id: string;
  credential_status: CredentialStatus;
  issued_at: string;
  expires_at: string;
  certificate_s3_key: string | null;
}

/**
 * Review session history item returned from GET /certifications/{pathway_id}/reviews
 */
interface ReviewSession {
  revision_number: number;
  status: string;
  submission_url: string;
  submitted_at: string;
  reviewed_at: string | null;
  reviewer_notes: string | null;
}

/**
 * Pathway detail page for a specific certification pathway.
 *
 * Shows the learner's Combined_Review_Session status with contextual
 * next actions, credential info when awarded, re-certification prompt
 * when expired/renewal-eligible, capstone submission form, and review history.
 *
 * Route: /dashboard/certifications/[pathway]
 * Requirements: 12.3, 12.4, 12.6
 */
export default function PathwayDetailPage() {
  const params = useParams<{ pathway: string }>();
  const pathwayId = params.pathway;

  const [candidate, setCandidate] = useState<CandidateRecord | null>(null);
  const [credential, setCredential] = useState<CredentialRecord | null>(null);
  const [reviews, setReviews] = useState<ReviewSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Capstone submission form state
  const [submissionUrl, setSubmissionUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  useEffect(() => {
    if (!pathwayId) return;

    const fetchData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Fetch candidate record and review history in parallel
        const [candidateRes, reviewsRes] = await Promise.all([
          apiClient.get<CandidateRecord>(
            `/certifications/${encodeURIComponent(pathwayId)}`
          ),
          apiClient.get<ReviewSession[]>(
            `/certifications/${encodeURIComponent(pathwayId)}/reviews`
          ),
        ]);

        if (candidateRes.error) {
          setError(candidateRes.error);
          return;
        }

        if (candidateRes.data) {
          setCandidate(candidateRes.data);

          // If awarded, fetch credential details
          if (candidateRes.data.candidate_status === 'AWARDED') {
            const credentialRes = await apiClient.get<CredentialRecord>(
              `/certifications/${encodeURIComponent(pathwayId)}/credential`
            );
            if (credentialRes.data) {
              setCredential(credentialRes.data);
            }
          }
        }

        if (reviewsRes.data) {
          setReviews(reviewsRes.data);
        }
      } catch {
        setError('Failed to load pathway details. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [pathwayId]);

  /**
   * Handle capstone submission form
   */
  async function handleSubmitCapstone(e: React.FormEvent) {
    e.preventDefault();

    if (!submissionUrl.trim()) return;

    setIsSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(false);

    try {
      const response = await apiClient.post(
        `/certifications/${encodeURIComponent(pathwayId)}/submit`,
        { submission_url: submissionUrl.trim() }
      );

      if (response.error) {
        setSubmitError(response.error);
        return;
      }

      setSubmitSuccess(true);
      setSubmissionUrl('');

      // Refresh data after submission
      const [candidateRes, reviewsRes] = await Promise.all([
        apiClient.get<CandidateRecord>(
          `/certifications/${encodeURIComponent(pathwayId)}`
        ),
        apiClient.get<ReviewSession[]>(
          `/certifications/${encodeURIComponent(pathwayId)}/reviews`
        ),
      ]);

      if (candidateRes.data) setCandidate(candidateRes.data);
      if (reviewsRes.data) setReviews(reviewsRes.data);
    } catch {
      setSubmitError('Failed to submit capstone. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  /**
   * Determine contextual action text based on review gate status
   */
  function getNextAction(status: ReviewStatus): string {
    switch (status) {
      case 'PENDING_SUBMISSION':
        return 'Submit your capstone project to begin the review process.';
      case 'PENDING_REVIEW':
        return 'Your submission is being reviewed. Expect someone to reach out within 24-48 hours.';
      case 'REVISIONS_REQUIRED':
        return 'Revisions are required. Please update your capstone and resubmit.';
      case 'PASSED':
        return 'Congratulations! Your review session passed.';
      case 'FAILED':
        return 'Your review session was not successful.';
      default:
        return '';
    }
  }

  /**
   * Check if capstone submission form should be shown
   */
  function shouldShowSubmissionForm(): boolean {
    if (!candidate) return false;
    const { status } = candidate.review_gate;
    const { candidate_status } = candidate;

    // Show for initial submission
    if (status === 'PENDING_SUBMISSION') return true;
    // Show for revisions
    if (status === 'REVISIONS_REQUIRED') return true;
    // Show for re-certification (RENEWAL_ELIGIBLE or EXPIRED)
    if (candidate_status === 'EXPIRED') return true;

    // Show if credential is RENEWAL_ELIGIBLE or EXPIRED
    if (credential) {
      if (
        credential.credential_status === 'RENEWAL_ELIGIBLE' ||
        credential.credential_status === 'EXPIRED'
      ) {
        return true;
      }
    }

    return false;
  }

  return (
    <AuthGuard>
      <div className="min-h-screen bg-white dark:bg-gray-950">
        <NavbarWithAuth />
        <main className="pt-16">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
            {/* Back link */}
            <Link
              href="/dashboard/certifications"
              className="inline-flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 mb-6"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
              Back to Certifications
            </Link>

            {/* Loading state */}
            {isLoading && (
              <div className="space-y-4">
                <div className="animate-pulse bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6">
                  <div className="h-6 bg-gray-200 dark:bg-gray-800 rounded w-64 mb-4" />
                  <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-full mb-2" />
                  <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-2/3" />
                </div>
              </div>
            )}

            {/* Error state */}
            {error && !isLoading && (
              <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-sm text-red-700 dark:text-red-400">
                  {error}
                </p>
              </div>
            )}

            {/* Main content */}
            {!isLoading && !error && candidate && (
              <div className="space-y-6">
                {/* Page header */}
                <div>
                  <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100">
                    {pathwayId
                      .split('-')
                      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                      .join(' ')}
                  </h1>
                  <p className="mt-2 text-gray-600 dark:text-gray-400">
                    {getNextAction(candidate.review_gate.status)}
                  </p>
                </div>

                {/* Review Session Status */}
                <section aria-labelledby="review-status-heading">
                  <h2
                    id="review-status-heading"
                    className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3"
                  >
                    Review Session Status
                  </h2>
                  <ReviewSessionStatus
                    status={candidate.review_gate.status}
                    pathway_id={pathwayId}
                  />
                </section>

                {/* Credential section — when AWARDED */}
                {candidate.candidate_status === 'AWARDED' && credential && (
                  <section aria-labelledby="credential-heading">
                    <h2
                      id="credential-heading"
                      className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3"
                    >
                      Your Credential
                    </h2>
                    <div className="space-y-4">
                      <CredentialBadge
                        credential_id={credential.credential_id}
                        credential_status={credential.credential_status}
                        issued_at={credential.issued_at}
                        expires_at={credential.expires_at}
                      />
                      <CertificateDownload
                        pathway_id={pathwayId}
                        disabled={!credential.certificate_s3_key}
                      />
                    </div>
                  </section>
                )}

                {/* Re-certification prompt — when RENEWAL_ELIGIBLE or EXPIRED */}
                {credential &&
                  (credential.credential_status === 'RENEWAL_ELIGIBLE' ||
                    credential.credential_status === 'EXPIRED') && (
                    <section aria-labelledby="recert-heading">
                      <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                        <h2
                          id="recert-heading"
                          className="text-base font-semibold text-amber-800 dark:text-amber-200 mb-1"
                        >
                          {credential.credential_status === 'RENEWAL_ELIGIBLE'
                            ? 'Credential Expiring Soon'
                            : 'Credential Expired'}
                        </h2>
                        <p className="text-sm text-amber-700 dark:text-amber-300">
                          {credential.credential_status === 'RENEWAL_ELIGIBLE'
                            ? 'Your credential is approaching expiration. Submit a new capstone to begin re-certification.'
                            : 'Your credential has expired. Submit a new capstone to begin re-certification and receive a fresh credential.'}
                        </p>
                      </div>
                    </section>
                  )}

                {/* Capstone submission form */}
                {shouldShowSubmissionForm() && (
                  <section aria-labelledby="submit-heading">
                    <h2
                      id="submit-heading"
                      className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3"
                    >
                      {candidate.review_gate.status === 'REVISIONS_REQUIRED'
                        ? 'Resubmit Capstone'
                        : 'Submit Capstone'}
                    </h2>
                    <form
                      onSubmit={handleSubmitCapstone}
                      className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-4 space-y-4"
                    >
                      <div>
                        <label
                          htmlFor="submission-url"
                          className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                        >
                          Repository URL
                        </label>
                        <input
                          id="submission-url"
                          type="url"
                          value={submissionUrl}
                          onChange={(e) => setSubmissionUrl(e.target.value)}
                          placeholder="https://github.com/username/capstone-project"
                          required
                          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                        />
                      </div>

                      {submitError && (
                        <p
                          className="text-sm text-red-600 dark:text-red-400"
                          role="alert"
                        >
                          {submitError}
                        </p>
                      )}

                      {submitSuccess && (
                        <p
                          className="text-sm text-green-600 dark:text-green-400"
                          role="status"
                        >
                          Capstone submitted successfully. Expect someone to
                          reach out within 24-48 hours.
                        </p>
                      )}

                      <button
                        type="submit"
                        disabled={isSubmitting || !submissionUrl.trim()}
                        className="inline-flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-gray-900 transition-colors hover:bg-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-amber-400 dark:hover:bg-amber-500 dark:focus:ring-offset-gray-950 min-h-[44px]"
                      >
                        {isSubmitting ? 'Submitting...' : 'Submit Capstone'}
                      </button>
                    </form>
                  </section>
                )}

                {/* Review history section */}
                {reviews.length > 0 && (
                  <section aria-labelledby="history-heading">
                    <h2
                      id="history-heading"
                      className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3"
                    >
                      Review History
                    </h2>
                    <div className="space-y-3">
                      {reviews.map((session) => (
                        <div
                          key={session.revision_number}
                          className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-4"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                  Revision {session.revision_number}
                                </span>
                                <StatusPill status={session.status} />
                              </div>
                              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 truncate">
                                {session.submission_url}
                              </p>
                              {session.reviewer_notes && (
                                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                                  {session.reviewer_notes}
                                </p>
                              )}
                            </div>
                            <div className="text-right text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                              <div>
                                Submitted:{' '}
                                {new Date(
                                  session.submitted_at
                                ).toLocaleDateString()}
                              </div>
                              {session.reviewed_at && (
                                <div>
                                  Reviewed:{' '}
                                  {new Date(
                                    session.reviewed_at
                                  ).toLocaleDateString()}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}

/**
 * Status pill for review session history items
 */
function StatusPill({ status }: { status: string }) {
  const styles: Record<string, string> = {
    PENDING_REVIEW:
      'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
    REVISIONS_REQUIRED:
      'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
    PASSED:
      'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
    FAILED: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  };

  const labels: Record<string, string> = {
    PENDING_REVIEW: 'Pending Review',
    REVISIONS_REQUIRED: 'Revisions Required',
    PASSED: 'Passed',
    FAILED: 'Failed',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${styles[status] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'}`}
    >
      {labels[status] || status}
    </span>
  );
}
