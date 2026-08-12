'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';

/**
 * Credential status type matching backend CredentialStatus enum.
 */
type CredentialStatus = 'ACTIVE' | 'RENEWAL_ELIGIBLE' | 'EXPIRED' | 'REVOKED';

/**
 * Public credential verification response from GET /public/credentials/{credential_id}.
 */
interface PublicCredentialResponse {
  credential_id: string;
  holder_name: string;
  pathway_name: string;
  issued_at: string;
  expires_at: string;
  credential_status: CredentialStatus;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * Status badge configuration for visual indicator per credential status.
 */
const STATUS_CONFIG: Record<
  CredentialStatus,
  { label: string; badgeClass: string; iconColor: string }
> = {
  ACTIVE: {
    label: 'Active',
    badgeClass: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300 border-green-200 dark:border-green-800',
    iconColor: 'text-green-500',
  },
  RENEWAL_ELIGIBLE: {
    label: 'Renewal Eligible',
    badgeClass: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300 border-yellow-200 dark:border-yellow-800',
    iconColor: 'text-yellow-500',
  },
  EXPIRED: {
    label: 'Expired',
    badgeClass: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400 border-gray-200 dark:border-gray-700',
    iconColor: 'text-gray-400',
  },
  REVOKED: {
    label: 'Revoked',
    badgeClass: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300 border-red-200 dark:border-red-800',
    iconColor: 'text-red-500',
  },
};

/**
 * Format an ISO date string to a human-friendly format.
 */
function formatDate(isoDate: string): string {
  try {
    const date = new Date(isoDate);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  } catch {
    return isoDate;
  }
}

/**
 * Public credential verification page.
 *
 * Route: /verify/{credentialId}
 *
 * This page is publicly accessible (no authentication required) and allows
 * third parties (e.g., employers) to verify a DSB credential. It fetches the
 * public verification endpoint and displays the credential details or a
 * 404-style message for invalid credential IDs.
 *
 * Requirements: 10.1, 10.2, 10.3
 */
export default function VerifyCredentialPage() {
  const params = useParams();
  const credentialId = params.credentialId as string;

  const [credential, setCredential] = useState<PublicCredentialResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCredential = async () => {
      if (!credentialId) {
        setNotFound(true);
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(
          `${API_BASE_URL}/public/credentials/${encodeURIComponent(credentialId)}`
        );

        if (response.status === 404) {
          setNotFound(true);
        } else if (!response.ok) {
          setError('Unable to verify credential at this time. Please try again later.');
        } else {
          const data: PublicCredentialResponse = await response.json();
          setCredential(data);
        }
      } catch {
        setError('Unable to connect to verification service. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchCredential();
  }, [credentialId]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Public header with DSB branding */}
      <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <img
              src="/light_mode_logo.svg"
              alt="The DevSec Blueprint"
              className="h-8 w-auto dark:hidden"
            />
            <img
              src="/dark_mode_logo.svg"
              alt="The DevSec Blueprint"
              className="h-8 w-auto hidden dark:block"
            />
          </Link>
          <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
            Credential Verification
          </span>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
        {/* Loading state */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="w-8 h-8 border-2 border-gray-300 dark:border-gray-700 border-t-yellow-500 rounded-full animate-spin" />
            <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
              Verifying credential...
            </p>
          </div>
        )}

        {/* Not found state */}
        {!isLoading && notFound && (
          <div className="text-center py-16">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 mb-6">
              <svg
                className="w-8 h-8 text-gray-400 dark:text-gray-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              Credential Not Found
            </h1>
            <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
              The credential ID{' '}
              <code className="text-sm bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded font-mono">
                {credentialId}
              </code>{' '}
              does not match any issued credential. Please check the ID and try again.
            </p>
            <Link
              href="/"
              className="inline-flex items-center mt-8 text-sm font-medium text-yellow-600 hover:text-yellow-700 dark:text-yellow-400 dark:hover:text-yellow-300"
            >
              &larr; Back to The DevSec Blueprint
            </Link>
          </div>
        )}

        {/* Error state */}
        {!isLoading && error && (
          <div className="text-center py-16">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-50 dark:bg-red-900/20 mb-6">
              <svg
                className="w-8 h-8 text-red-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
                />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              Verification Unavailable
            </h1>
            <p className="text-gray-600 dark:text-gray-400">{error}</p>
          </div>
        )}

        {/* Credential verified state */}
        {!isLoading && credential && (
          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl shadow-sm overflow-hidden">
            {/* Verified banner */}
            <div className="px-6 py-4 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-800 flex items-center gap-3">
              <svg
                className={`w-5 h-5 shrink-0 ${STATUS_CONFIG[credential.credential_status].iconColor}`}
                fill="currentColor"
                viewBox="0 0 20 20"
                aria-hidden="true"
              >
                {credential.credential_status === 'ACTIVE' ? (
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                    clipRule="evenodd"
                  />
                ) : credential.credential_status === 'REVOKED' ? (
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
                    clipRule="evenodd"
                  />
                ) : (
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z"
                    clipRule="evenodd"
                  />
                )}
              </svg>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                DSB Credential Verification
              </span>
            </div>

            {/* Credential details */}
            <div className="px-6 py-8">
              {/* Status badge */}
              <div className="flex justify-center mb-6">
                <span
                  className={`inline-flex items-center rounded-full border px-4 py-1.5 text-sm font-semibold ${STATUS_CONFIG[credential.credential_status].badgeClass}`}
                  aria-label={`Credential status: ${STATUS_CONFIG[credential.credential_status].label}`}
                >
                  {STATUS_CONFIG[credential.credential_status].label}
                </span>
              </div>

              {/* Holder name */}
              <h2 className="text-center text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1">
                {credential.holder_name}
              </h2>

              {/* Pathway name */}
              <p className="text-center text-base text-gray-600 dark:text-gray-400 mb-8">
                {credential.pathway_name}
              </p>

              {/* Credential details grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 border-t border-gray-100 dark:border-gray-800 pt-6">
                <div>
                  <dt className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-500">
                    Credential ID
                  </dt>
                  <dd className="mt-1 text-sm font-mono text-gray-900 dark:text-gray-200">
                    {credential.credential_id}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-500">
                    Status
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-gray-200">
                    {STATUS_CONFIG[credential.credential_status].label}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-500">
                    Issued
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-gray-200">
                    {formatDate(credential.issued_at)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-500">
                    Expires
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-gray-200">
                    {formatDate(credential.expires_at)}
                  </dd>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-800">
              <p className="text-xs text-center text-gray-500 dark:text-gray-500">
                This credential was issued by The DevSec Blueprint. Verify at{' '}
                <span className="font-mono">devsecblueprint.com/verify/{credential.credential_id}</span>
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Minimal footer */}
      <footer className="border-t border-gray-200 dark:border-gray-800 mt-auto">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 text-center">
          <p className="text-xs text-gray-500 dark:text-gray-500">
            &copy; {new Date().getFullYear()} The DevSec Blueprint. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
