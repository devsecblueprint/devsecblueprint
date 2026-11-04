'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Footer } from '@/components/layout/Footer';
import { useAuth } from '@/lib/hooks/useAuth';
import { apiClient } from '@/lib/api';

/**
 * Student academic-email verification page.
 *
 * Requires authentication (mirrors the pricing page's login-redirect pattern).
 * Submits an academic email to POST /api/verification/student/submit and maps
 * each backend status code to a friendly message (Requirements 4.2, 8.11, 8.12).
 */
export default function StudentVerifyPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Redirect unauthenticated visitors to login, returning here afterwards.
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login?returnTo=/pricing/verify');
    }
  }, [authLoading, isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const academicEmail = email.trim();
    if (!academicEmail) {
      setError('Please enter your academic email address.');
      return;
    }

    setSubmitting(true);
    setError(null);

    const { statusCode, error: apiError } = await apiClient.post(
      '/api/verification/student/submit',
      { academic_email: academicEmail }
    );

    setSubmitting(false);

    // 202 Accepted — verification email is on its way.
    if (statusCode === 202) {
      setSubmitted(true);
      return;
    }

    // Map known error statuses to friendly messages (Requirement 4.2).
    switch (statusCode) {
      case 400:
        setError('That doesn\u2019t look like a valid email address. Please check and try again.');
        break;
      case 422:
        setError(
          'That email isn\u2019t recognized as an academic address. Please use your school-issued email.'
        );
        break;
      case 429:
        setError('Too many attempts. Please wait a little while before trying again.');
        break;
      case 502:
        setError('We couldn\u2019t send the verification email right now. Please try again shortly.');
        break;
      case 503:
        setError('The verification service is temporarily unavailable. Please try again shortly.');
        break;
      default:
        setError(apiError || 'Something went wrong. Please try again.');
    }
  };

  // Avoid flashing the form while auth is resolving or a redirect is pending.
  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-950 flex flex-col">
        <NavbarWithAuth />
        <main className="flex-1 pt-16">
          <div className="max-w-xl mx-auto px-4 sm:px-6 py-16 sm:py-20">
            <div className="animate-pulse bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-3xl p-8">
              <div className="h-7 w-48 bg-gray-200 dark:bg-gray-700 rounded-sm mb-4" />
              <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded-sm mb-2" />
              <div className="h-4 w-2/3 bg-gray-200 dark:bg-gray-700 rounded-sm mb-8" />
              <div className="h-12 w-full bg-gray-200 dark:bg-gray-700 rounded-xl" />
            </div>
          </div>
        </main>
        <Footer variant="minimal" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 flex flex-col">
      <NavbarWithAuth />

      <main className="flex-1 pt-16">
        <div className="max-w-xl mx-auto px-4 sm:px-6 py-16 sm:py-20">
          <div className="text-center mb-10">
            <span className="inline-block px-3 py-1.5 text-xs font-semibold uppercase tracking-wide rounded-full bg-sky-50 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300 mb-5">
              Student Builder
            </span>
            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              Verify your student status
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Enter your academic email and we&apos;ll send you a link to confirm your eligibility for
              discounted Builder pricing.
            </p>
          </div>

          {submitted ? (
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
              <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                Check your email
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                We sent a verification link to{' '}
                <span className="font-medium text-gray-900 dark:text-gray-100">{email.trim()}</span>.
                Open it to confirm your academic eligibility. The link expires in 24 hours.
              </p>
              <button
                type="button"
                onClick={() => {
                  setSubmitted(false);
                  setError(null);
                }}
                className="text-sm text-sky-600 dark:text-sky-400 underline hover:no-underline"
              >
                Use a different email
              </button>
            </div>
          ) : (
            <form
              onSubmit={handleSubmit}
              className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-3xl p-8"
            >
              {error && (
                <div
                  role="alert"
                  className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl"
                >
                  <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
                </div>
              )}

              <label
                htmlFor="academic-email"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                Academic email
              </label>
              <input
                id="academic-email"
                type="email"
                name="academic_email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@university.edu"
                className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
              />

              <button
                type="submit"
                disabled={submitting}
                className="w-full mt-6 py-4 px-6 text-center rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-semibold text-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Sending verification email...' : 'Send verification email'}
              </button>

              <p className="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
                Changed your mind?{' '}
                <Link
                  href="/pricing"
                  className="text-sky-600 dark:text-sky-400 underline hover:no-underline"
                >
                  Back to pricing
                </Link>
              </p>
            </form>
          )}
        </div>
      </main>

      <Footer variant="minimal" />
    </div>
  );
}
