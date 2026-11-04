'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';

/**
 * Minimal product shape consumed by the Student Discount card. Mirrors the
 * `Product` interface used by the pricing page's `/api/stripe/products` fetch.
 */
export interface StudentDiscountProduct {
  id: string;
  name: string;
  description: string;
  price: number;
  monthly_price: number;
  currency: string;
  interval: string;
  dsb_tier: string;
  price_id: string;
}

interface StudentDiscountCardProps {
  /** Student Builder monthly product (dsb_tier === 'STUDENT_BUILDER', interval === 'month'). */
  studentMonthly: StudentDiscountProduct | null;
  /** Student Builder annual product (dsb_tier === 'STUDENT_BUILDER', interval === 'year'). */
  studentAnnual: StudentDiscountProduct | null;
  /** Standard Builder monthly product, used for the student-vs-Builder savings heading. */
  builderMonthly: StudentDiscountProduct | null;
  /** Standard Builder annual product, used for the student-vs-Builder savings heading. */
  builderAnnual: StudentDiscountProduct | null;
  /** True while products are still loading from the API. */
  isLoading: boolean;
  /** Whether the current visitor is signed in (from useAuth). */
  isAuthenticated: boolean;
  /** True while authentication state is still resolving (from useAuth). */
  authLoading: boolean;
  /**
   * The visitor's current subscription status (e.g. 'active', 'past_due', or
   * null when there is no subscription). Sourced from the pricing page's
   * `/api/stripe/subscription` fetch so the card does not refetch it.
   */
  subscriptionStatus: string | null;
}

function formatPrice(price: number, currency: string): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.toUpperCase(),
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(price / 100);
}

/**
 * Student-vs-Builder savings percent for a shared interval, rounded to the
 * nearest 5%. Returns null when inputs are unusable (Requirement 8.8/8.9,
 * Property 15): N = round(((b - s) / b) * 100 / 5) * 5.
 */
export function computeStudentSavingsPercent(
  builderPrice: number | undefined,
  studentPrice: number | undefined
): number | null {
  if (
    builderPrice === undefined ||
    studentPrice === undefined ||
    !(builderPrice > 0) ||
    studentPrice < 0 ||
    studentPrice > builderPrice
  ) {
    return null;
  }
  return Math.round(((builderPrice - studentPrice) / builderPrice) * 100 / 5) * 5;
}

/**
 * Dynamic annual-savings percent computed from the student monthly vs annual
 * prices (Requirement 8.7): 1 - (annual.monthly_price / monthly.price).
 */
function computeAnnualSavingsPercent(
  studentMonthly: StudentDiscountProduct | null,
  studentAnnual: StudentDiscountProduct | null
): number | null {
  if (!studentMonthly || !studentAnnual) return null;
  if (!(studentMonthly.price > 0)) return null;
  const ratio = studentAnnual.monthly_price / studentMonthly.price;
  const percent = Math.round((1 - ratio) * 100);
  return percent > 0 ? percent : null;
}

export function StudentDiscountCard({
  studentMonthly,
  studentAnnual,
  builderMonthly,
  builderAnnual,
  isLoading,
  isAuthenticated,
  authLoading,
  subscriptionStatus,
}: StudentDiscountCardProps) {
  const router = useRouter();
  const [billingInterval, setBillingInterval] = useState<'month' | 'year'>('month');

  // Active Student Builder eligibility for the signed-in visitor. `null` while
  // unknown/unfetched; once fetched it reflects the `eligible` flag from
  // GET /api/verification/student/eligibility (Requirement 4.7/4.8).
  const [eligible, setEligible] = useState<boolean | null>(null);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [ctaError, setCtaError] = useState<string | null>(null);

  // Fetch the visitor's eligibility once authenticated. Unauthenticated
  // visitors never need it (their CTA always routes through login → verify),
  // and `canCheckout` below is gated on `isAuthenticated` so any stale value
  // left over from a previous signed-in session can never enable checkout.
  useEffect(() => {
    if (!isAuthenticated || authLoading) return;

    let cancelled = false;

    async function fetchEligibility() {
      const { data } = await apiClient.get<{ eligible: boolean; expires_at: string | null }>(
        '/api/verification/student/eligibility'
      );
      if (!cancelled) {
        setEligible(data ? Boolean(data.eligible) : false);
      }
    }

    fetchEligibility();
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, authLoading]);

  // Loading skeleton matches the Builder card's skeleton conventions.
  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-3xl p-8 lg:p-10 animate-pulse">
        <div className="h-7 w-28 bg-gray-200 dark:bg-gray-700 rounded-full mb-5" />
        <div className="h-9 w-40 bg-gray-200 dark:bg-gray-700 rounded-sm mb-2" />
        <div className="h-5 w-64 bg-gray-200 dark:bg-gray-700 rounded-sm mb-6" />
        <div className="h-14 w-36 bg-gray-200 dark:bg-gray-700 rounded-sm mb-6" />
        <div className="space-y-3">
          <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded-sm" />
          <div className="h-4 w-5/6 bg-gray-200 dark:bg-gray-700 rounded-sm" />
        </div>
        <div className="h-14 w-full bg-gray-200 dark:bg-gray-700 rounded-xl mt-10" />
      </div>
    );
  }

  const hasStudentPrice = Boolean(studentMonthly || studentAnnual);

  // Discovery failure / no price (Requirement 8.10): render a temporarily
  // unavailable state with no hardcoded or stale price.
  if (!hasStudentPrice) {
    return (
      <div className="bg-white dark:bg-gray-900 border border-sky-300 dark:border-sky-500/40 rounded-3xl p-8 lg:p-10 flex flex-col">
        <div className="flex-1">
          <span className="inline-block px-3 py-1.5 text-xs font-semibold uppercase tracking-wide rounded-full bg-sky-50 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300 mb-5">
            Student Builder
          </span>
          <h2 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Student Builder
          </h2>
          <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
            Everything included with Builder, at a discounted rate for students.
          </p>
          <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700 rounded-lg">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              The student discount is temporarily unavailable. Please check back soon.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Selected student price row for the active interval. Fall back to whichever
  // interval exists so a single-interval catalog still renders a real price.
  const selectedStudent =
    billingInterval === 'year'
      ? (studentAnnual ?? studentMonthly)
      : (studentMonthly ?? studentAnnual);

  const bothIntervalsAvailable = Boolean(studentMonthly && studentAnnual);
  const annualSavings = computeAnnualSavingsPercent(studentMonthly, studentAnnual);

  // Student-vs-Builder savings heading for the SAME interval (Requirement 8.8).
  // Omit the computed percent when the two tiers don't share a common interval
  // for the selected toggle (Requirement 8.9).
  const builderForInterval = billingInterval === 'year' ? builderAnnual : builderMonthly;
  const studentForInterval = billingInterval === 'year' ? studentAnnual : studentMonthly;
  const savingsPercent = computeStudentSavingsPercent(
    builderForInterval?.price,
    studentForInterval?.price
  );

  const savingsHeading =
    savingsPercent !== null
      ? `Students save ~${savingsPercent}% on Builder`
      : 'Discounted Builder pricing for students';

  const isAnnual = billingInterval === 'year';
  const billingNote = isAnnual
    ? 'Billed annually. Cancel anytime.'
    : 'Billed monthly. Cancel anytime.';

  // --- CTA state machine (Requirements 8.11–8.14) ---------------------------
  // A visitor with an existing active/past_due subscription must not be able to
  // start a duplicate membership (8.14) — the CTA is hidden in that case.
  const hasActiveSubscription =
    subscriptionStatus === 'active' || subscriptionStatus === 'past_due';

  // Signed in, eligible, and no active/past_due subscription → checkout (8.13).
  const canCheckout = isAuthenticated && eligible === true && !hasActiveSubscription;

  const ctaLabel = canCheckout ? 'Subscribe as Student' : 'Verify Student Status';

  // Not-signed-in CTA routes to login and continues into the verification flow
  // after sign-in (8.11). Signed-in-but-not-eligible starts the verification
  // flow directly (8.12). Matches page.tsx's `/login?returnTo=...` pattern.
  const handleCtaClick = async () => {
    setCtaError(null);

    if (!isAuthenticated) {
      router.push('/login?returnTo=/pricing/verify');
      return;
    }

    if (!canCheckout) {
      router.push('/pricing/verify');
      return;
    }

    // Eligible, no active/past_due subscription → start Student Builder checkout
    // for the selected billing interval (8.13).
    if (!selectedStudent) return;

    setCheckoutLoading(true);
    const { data, error } = await apiClient.post<{ checkout_url: string }>(
      '/api/stripe/checkout',
      {
        price_id: selectedStudent.price_id,
        dsb_tier: 'STUDENT_BUILDER',
        interval: billingInterval,
      }
    );

    if (data?.checkout_url) {
      window.location.href = data.checkout_url;
    } else {
      setCtaError(error || 'Failed to start checkout. Please try again.');
      setCheckoutLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-900 border border-sky-300 dark:border-sky-500/40 rounded-3xl p-8 lg:p-10 flex flex-col">
      <div className="flex-1">
        {/* Eyebrow row — grad-cap icon folded in with the tier identity */}
        <div className="flex items-center gap-3 mb-5">
          <span className="w-10 h-10 shrink-0 rounded-xl bg-sky-100 dark:bg-sky-500/15 flex items-center justify-center">
            <svg
              className="w-6 h-6 text-sky-600 dark:text-sky-400"
              fill="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path d="M11.7 2.805a.75.75 0 01.6 0A60.65 60.65 0 0122.83 8.72a.75.75 0 01-.231 1.337 49.948 49.948 0 00-9.902 3.912l-.003.002c-.114.06-.23.117-.346.17a.75.75 0 01-.646 0 51.082 51.082 0 00-.396-.198 50.69 50.69 0 00-2.159-.982V11.3a.75.75 0 01.387-.657 50.5 50.5 0 013.498-1.773.75.75 0 00-.598-1.375 52.006 52.006 0 00-3.467 1.76.75.75 0 01-.73-.001 50.456 50.456 0 00-5.052-2.558.75.75 0 01-.231-1.337A60.654 60.654 0 0111.7 2.805z" />
              <path d="M13.06 15.473a48.45 48.45 0 017.666-3.282c.134 1.414.22 2.843.255 4.284a.75.75 0 01-.46.711 47.87 47.87 0 00-8.105 4.342.75.75 0 01-.832 0 47.87 47.87 0 00-8.104-4.342.75.75 0 01-.461-.71c.035-1.442.121-2.872.255-4.286.921.304 1.83.634 2.726.99v1.27a1.5 1.5 0 00-.14 2.508c-.09.38-.222.753-.397 1.11.452.213.901.434 1.346.661a6.729 6.729 0 00.551-1.608 1.5 1.5 0 00.14-2.67v-.645a48.549 48.549 0 013.44 1.667 2.25 2.25 0 002.12 0z" />
              <path d="M4.462 19.462c.42-.419.753-.89 1-1.395.453.214.902.435 1.347.662a6.742 6.742 0 01-1.286 1.794.75.75 0 11-1.06-1.06z" />
            </svg>
          </span>
          {/* Eyebrow */}
          <span className="inline-block w-fit px-3 py-1.5 text-xs font-semibold uppercase tracking-wide rounded-full bg-sky-50 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300">
            Student Builder
          </span>
        </div>

        {/* Name */}
        <h2 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Student Builder
        </h2>

        {/* Summary */}
        <p className="text-lg text-gray-600 dark:text-gray-400 mb-4">
          Everything included with Builder, at a discounted rate for students.
        </p>

        {/* Savings highlight — prominent near the top */}
        <h3 className="text-xl lg:text-2xl font-bold text-sky-700 dark:text-sky-300 mb-6">
          {savingsHeading}
        </h3>

        {/* Billing interval toggle */}
        {bothIntervalsAvailable && (
          <div className="flex items-center gap-3 mb-4">
            <button
              onClick={() => setBillingInterval('month')}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                billingInterval === 'month'
                  ? 'bg-sky-100 text-sky-800 dark:bg-sky-500/20 dark:text-sky-300'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingInterval('year')}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                billingInterval === 'year'
                  ? 'bg-sky-100 text-sky-800 dark:bg-sky-500/20 dark:text-sky-300'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Annual
              {annualSavings !== null && (
                <span className="ml-1.5 text-xs font-semibold text-green-600 dark:text-green-400">
                  Save {annualSavings}%
                </span>
              )}
            </button>
          </div>
        )}

        {/* Selected price + interval */}
        <div className="mb-2">
          {selectedStudent && isAnnual && studentAnnual ? (
            <>
              <span className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-gray-100">
                {formatPrice(studentAnnual.price, studentAnnual.currency)}
              </span>
              <span className="text-lg text-gray-500 dark:text-gray-400 ml-2">/year</span>
              <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {formatPrice(studentAnnual.monthly_price, studentAnnual.currency)}/mo equivalent
              </div>
            </>
          ) : selectedStudent ? (
            <>
              <span className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-gray-100">
                {formatPrice(selectedStudent.monthly_price, selectedStudent.currency)}
              </span>
              <span className="text-lg text-gray-500 dark:text-gray-400 ml-2">/month</span>
            </>
          ) : null}
        </div>

        {/* Billing note appropriate to the selected interval */}
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">{billingNote}</p>

        {/* Supporting copy */}
        <p className="text-base text-gray-600 dark:text-gray-400 leading-relaxed mb-6">
          Verify your academic email to get discounted Builder pricing. Same benefits. Lower
          student rate.
        </p>
      </div>

      {/* CTA — auth/eligibility-aware state machine (Requirements 8.11–8.14).
          Hidden entirely for members with an active/past_due subscription
          to prevent initiating a duplicate membership (8.14). Pinned to the
          bottom via mt-auto so the card height matches Free/Builder. */}
      {!hasActiveSubscription && (
        <div className="mt-auto pt-4">
          <button
            type="button"
            onClick={handleCtaClick}
            disabled={checkoutLoading}
            className="w-full py-4 px-6 text-center rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-semibold text-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {checkoutLoading ? 'Redirecting to checkout...' : ctaLabel}
          </button>
          {ctaError && (
            <p className="mt-2 text-sm text-red-600 dark:text-red-400" role="alert">
              {ctaError}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default StudentDiscountCard;
