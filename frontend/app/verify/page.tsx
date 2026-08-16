'use client';

import { useState } from 'react';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';

type CredentialStatus = 'ACTIVE' | 'RENEWAL_ELIGIBLE' | 'EXPIRED' | 'REVOKED';

interface PublicCredentialResponse {
  credential_id: string;
  holder_name: string;
  pathway_name: string;
  issued_at: string;
  expires_at: string;
  credential_status: CredentialStatus;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

function formatDate(isoDate: string): string {
  try {
    return new Date(isoDate).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  } catch {
    return isoDate;
  }
}

function getStatusConfig(status: CredentialStatus) {
  switch (status) {
    case 'ACTIVE':
      return {
        label: 'Active',
        message: 'This credential is valid and active.',
        bgClass: 'bg-green-50 dark:bg-green-900/10',
        borderClass: 'border-green-200 dark:border-green-800',
        textClass: 'text-green-700 dark:text-green-300',
        badgeClass: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300 border-green-200 dark:border-green-700',
        icon: '✓',
      };
    case 'RENEWAL_ELIGIBLE':
      return {
        label: 'Renewal Eligible',
        message: 'This credential is valid but approaching its expiration date.',
        bgClass: 'bg-amber-50 dark:bg-amber-900/10',
        borderClass: 'border-amber-200 dark:border-amber-800',
        textClass: 'text-amber-700 dark:text-amber-300',
        badgeClass: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300 border-amber-200 dark:border-amber-700',
        icon: '⏱',
      };
    case 'EXPIRED':
      return {
        label: 'Expired',
        message: 'This credential has expired and is no longer active.',
        bgClass: 'bg-gray-50 dark:bg-gray-900/50',
        borderClass: 'border-gray-200 dark:border-gray-700',
        textClass: 'text-gray-600 dark:text-gray-400',
        badgeClass: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400 border-gray-200 dark:border-gray-700',
        icon: '○',
      };
    case 'REVOKED':
      return {
        label: 'Revoked',
        message: 'This credential has been revoked and is no longer valid.',
        bgClass: 'bg-red-50 dark:bg-red-900/10',
        borderClass: 'border-red-200 dark:border-red-800',
        textClass: 'text-red-700 dark:text-red-300',
        badgeClass: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300 border-red-200 dark:border-red-700',
        icon: '✗',
      };
  }
}

export default function VerifyCredentialPage() {
  const [inputValue, setInputValue] = useState('');
  const [credential, setCredential] = useState<PublicCredentialResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    const credentialId = inputValue.trim();
    if (!credentialId) return;

    setIsLoading(true);
    setCredential(null);
    setNotFound(false);
    setError(null);
    setHasSearched(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/public/credentials/${encodeURIComponent(credentialId)}`,
        { credentials: 'include' }
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

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      <NavbarWithAuth />
      <main className="pt-16">
        <div className="max-w-xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
          {/* Page header */}
          <div className="text-center mb-8">
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              Verify a Credential
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Confirm the authenticity of a DSB certification credential.
            </p>
          </div>

          {/* Search form */}
          <form onSubmit={handleVerify} className="flex gap-2 mb-8">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Enter credential ID (e.g. DSB-DSEP-8F4C92A1)"
              className="flex-1 px-4 py-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent text-sm"
              aria-label="Credential ID"
            />
            <button
              type="submit"
              disabled={isLoading || !inputValue.trim()}
              className="px-5 py-3 rounded-lg bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold text-sm hover:bg-amber-600 dark:hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
            >
              {isLoading ? 'Verifying...' : 'Verify'}
            </button>
          </form>

          {/* Loading */}
          {isLoading && (
            <div className="flex flex-col items-center py-12">
              <div className="w-6 h-6 border-2 border-gray-300 dark:border-gray-700 border-t-amber-500 rounded-full animate-spin" />
              <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">Verifying...</p>
            </div>
          )}

          {/* Not found */}
          {!isLoading && notFound && (
            <div className="text-center py-10 px-4 rounded-lg border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">No credential found</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                <code className="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded font-mono">{inputValue.trim()}</code> does not match any issued credential.
              </p>
            </div>
          )}

          {/* Error */}
          {!isLoading && error && (
            <div className="text-center py-10 px-4 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10">
              <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
            </div>
          )}

          {/* Credential found — premium/official result */}
          {!isLoading && credential && (() => {
            const config = getStatusConfig(credential.credential_status);
            return (
              <div className="space-y-4">
                {/* Status banner */}
                <div className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${config.borderClass} ${config.bgClass}`}>
                  <span className={`text-lg ${config.textClass}`}>{config.icon}</span>
                  <div>
                    <p className={`text-sm font-semibold ${config.textClass}`}>{config.label}</p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">{config.message}</p>
                  </div>
                </div>

                {/* Credential card */}
                <div className="rounded-lg border border-gray-200 dark:border-gray-800 divide-y divide-gray-100 dark:divide-gray-800">
                  {/* Holder & pathway */}
                  <div className="px-5 py-5">
                    <p className="text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-500 mb-1">Credential Holder</p>
                    <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{credential.holder_name}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">{credential.pathway_name}</p>
                  </div>

                  {/* Details */}
                  <div className="px-5 py-4 grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-500 mb-0.5">Credential ID</p>
                      <p className="text-sm font-mono text-gray-900 dark:text-gray-100">{credential.credential_id}</p>
                    </div>
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-500 mb-0.5">Status</p>
                      <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${config.badgeClass}`}>
                        {config.label}
                      </span>
                    </div>
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-500 mb-0.5">Issued</p>
                      <p className="text-sm text-gray-900 dark:text-gray-100">{formatDate(credential.issued_at)}</p>
                    </div>
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-500 mb-0.5">Expires</p>
                      <p className="text-sm text-gray-900 dark:text-gray-100">{formatDate(credential.expires_at)}</p>
                    </div>
                  </div>

                  {/* Footer */}
                  <div className="px-5 py-3 bg-gray-50 dark:bg-gray-900/50">
                    <p className="text-[11px] text-gray-500 dark:text-gray-500">
                      Issued by The DevSec Blueprint · <a href="/" className="hover:text-amber-600 dark:hover:text-amber-400 underline">devsecblueprint.com</a>
                    </p>
                  </div>
                </div>
              </div>
            );
          })()}

          {/* Hint when nothing searched yet */}
          {!hasSearched && !isLoading && (
            <p className="text-center text-xs text-gray-400 dark:text-gray-500 mt-4">
              Credential IDs look like <code className="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded font-mono">DSB-DSEP-8F4C92A1</code>
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
