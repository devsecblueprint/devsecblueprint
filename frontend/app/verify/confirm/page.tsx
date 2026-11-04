'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Footer } from '@/components/layout/Footer';
import { apiClient } from '@/lib/api';

interface ConfirmResponse {
  eligible: boolean;
  expires_at: string | null;
}

type ConfirmState = 'loading' | 'success' | 'error';

/**
 * Confirm_Page content — reads the `token` query param (the raw token carried
 * in the verification email at /verify/confirm?token=...), posts it to
 * POST /api/verification/student/confirm, and renders the result.
 *
 * On success it shows the "Subscribe as Student" CTA, which links back to
 * /pricing where the StudentDiscountCard CTA now reads "Subscribe as Student"
 * for an eligible, signed-in visitor (Requirements 4.4, 8.11, 8.12, 8.13).
 */
function ConfirmContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  // Derive the initial view from the token synchronously (no effect-driven
  // setState for the missing-token case): a missing token is an immediate
  // error, a present token starts in the loading state while we POST.
  const [state, setState] = useState<ConfirmState>(token ? 'loading' : 'error');
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(
    token
      ? null
      : 'This confirmation link is missing its token. Please start the verification again.'
  );

  const confirm = useCallback(async () => {
    if (!token) return;

    const { data, statusCode, error } = await apiClient.post<ConfirmResponse>(
      '/api/verification/student/confirm',
      { token }
    );

    // 200 — eligibility confirmed.
    if (statusCode === 200 && data?.eligible) {
      setExpiresAt(data.expires_at);
      setState('success');
      return;
    }

    // 400 — invalid, expired, or already-used token.
    if (statusCode === 400) {
      setErrorMessage(
        'This verification link is invalid or has expired. Please request a new one.'
      );
      setState('error');
      return;
    }

    setErrorMessage(error || 'We couldn\u2019t confirm your verification. Please try again.');
    setState('error');
  }, [token]);

  // Attempt confirmation automatically once the token is read from the URL.
  // confirm() only updates state after an awaited call, so this does not
  // trigger synchronous cascading renders.
  useEffect(() => {
    confirm();
  }, [confirm]);

  const formatExpiry = (iso: string | null): string | null => {
    if (!iso) return null;
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return null;
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 flex flex-col">
      <NavbarWithAuth />

      <main className="flex-1 pt-16">
        <div className="max-w-xl mx-auto px-4 sm:px-6 py-16 sm:py-20">
          {state === 'loading' && (
            <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-3xl p-8 text-center">
              <div className="w-12 h-12 mx-auto mb-5 rounded-full border-4 border-sky-200 dark:border-sky-500/30 border-t-sky-600 dark:border-t-sky-400 animate-spin" />
              <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                Confirming your verification
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Hang tight while we check your academic eligibility.
              </p>
            </div>
          )}

          {state === 'success' && (
            <div className="bg-white dark:bg-gray-900 border border-green-300 dark:border-green-500/40 rounded-3xl p-8 text-center">
              <div className="w-12 h-12 mx-auto rounded-full bg-green-100 dark:bg-green-500/15 flex items-center justify-center mb-5">
                <svg
                  className="w-6 h-6 text-green-600 dark:text-green-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                You&apos;re verified
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mb-2">
                Your student status is confirmed. You can now subscribe at the discounted Builder rate.
              </p>
              {formatExpiry(expiresAt) && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                  Eligibility valid through {formatExpiry(expiresAt)}.
                </p>
              )}
              <Link
                href="/pricing"
                className="inline-block w-full py-4 px-6 text-center rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-semibold text-lg transition-colors"
              >
                Subscribe as Student
              </Link>
            </div>
          )}

          {state === 'error' && (
            <div className="bg-white dark:bg-gray-900 border border-red-300 dark:border-red-500/40 rounded-3xl p-8 text-center">
              <div className="w-12 h-12 mx-auto rounded-full bg-red-100 dark:bg-red-500/15 flex items-center justify-center mb-5">
                <svg
                  className="w-6 h-6 text-red-600 dark:text-red-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                Verification failed
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {errorMessage}
              </p>
              <Link
                href="/pricing/verify"
                className="inline-block w-full py-4 px-6 text-center rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-semibold text-lg transition-colors"
              >
                Retry verification
              </Link>
            </div>
          )}
        </div>
      </main>

      <Footer variant="minimal" />
    </div>
  );
}

/**
 * Wrapper page component with a Suspense boundary for useSearchParams().
 * Next.js static export requires useSearchParams() to be wrapped in Suspense.
 */
export default function StudentVerifyConfirmPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-white dark:bg-gray-950 flex flex-col">
          <NavbarWithAuth />
          <main className="flex-1 pt-16">
            <div className="max-w-xl mx-auto px-4 sm:px-6 py-16 sm:py-20">
              <div className="animate-pulse bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-3xl p-8">
                <div className="h-6 w-48 bg-gray-200 dark:bg-gray-700 rounded-sm mb-4 mx-auto" />
                <div className="h-4 w-2/3 bg-gray-200 dark:bg-gray-700 rounded-sm mx-auto" />
              </div>
            </div>
          </main>
          <Footer variant="minimal" />
        </div>
      }
    >
      <ConfirmContent />
    </Suspense>
  );
}
