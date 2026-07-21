'use client';

import { useState, useEffect, useCallback } from 'react';
import { AuthGuard } from '@/components/AuthGuard';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { apiClient } from '@/lib/api';

/**
 * Subscription status response from GET /api/stripe/subscription
 */
interface SubscriptionStatus {
  membership_tier: string;
  subscription_status: string | null;
  current_period_end: string | null;
  stripe_subscription_id: string | null;
}

/**
 * Format a tier name for display
 */
function formatTierName(tier: string): string {
  switch (tier) {
    case 'FREE':
      return 'Free Plan';
    case 'EXPLORER':
      return 'Explorer';
    case 'BUILDER':
      return 'Builder';
    case 'BUILDER_ACADEMY':
      return 'Builder Academy';
    default:
      return tier;
  }
}

/**
 * Get a badge color class based on subscription status
 */
function getStatusColor(status: string | null): string {
  switch (status) {
    case 'active':
      return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
    case 'past_due':
      return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
    case 'canceled':
      return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400';
    case 'incomplete':
      return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
    default:
      return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400';
  }
}

/**
 * Subscription Settings Page
 * 
 * Displays the user's current subscription tier and allows managing
 * the subscription through Stripe's Customer Portal.
 */
export default function SubscriptionPage() {
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRedirecting, setIsRedirecting] = useState(false);

  const fetchSubscription = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    const { data, error: apiError } = await apiClient.get<SubscriptionStatus>('/api/stripe/subscription');
    if (apiError) {
      setError(apiError);
    } else if (data) {
      setSubscription(data);
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    fetchSubscription();
  }, [fetchSubscription]);

  const handleManageSubscription = async () => {
    setIsRedirecting(true);
    const { data, error: portalError } = await apiClient.post<{ portal_url: string }>('/api/stripe/portal', {});
    if (portalError) {
      setError(portalError);
      setIsRedirecting(false);
    } else if (data?.portal_url) {
      window.location.href = data.portal_url;
    }
  };

  const isFree = !subscription || subscription.membership_tier === 'FREE';
  const isCanceled = subscription?.subscription_status === 'canceled';

  return (
    <AuthGuard>
      <div className="min-h-screen bg-white dark:bg-gray-950">
        <NavbarWithAuth />
        <main className="pt-16">
          <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              Subscription
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mb-8">
              Manage your membership plan and billing.
            </p>

            {/* Error Banner */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
              </div>
            )}

            {/* Subscription Card */}
            <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6">
              {isLoading ? (
                /* Loading skeleton */
                <div className="animate-pulse space-y-4">
                  <div className="h-6 bg-gray-200 dark:bg-gray-800 rounded w-40" />
                  <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-56" />
                  <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-32" />
                </div>
              ) : isFree ? (
                /* FREE tier */
                <div>
                  <div className="flex items-center gap-3 mb-3">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                      Free Plan
                    </h2>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400">
                      Current
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                    You are currently on the free plan. Upgrade to unlock premium features and Discord role benefits.
                  </p>
                  <a
                    href="/pricing"
                    className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-amber-500 rounded-lg hover:bg-amber-600 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                    View Pricing Plans
                  </a>
                </div>
              ) : (
                /* Active/Canceled subscription */
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                      {formatTierName(subscription!.membership_tier)}
                    </h2>
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                        subscription!.subscription_status
                      )}`}
                    >
                      {isCanceled ? 'Canceling' : subscription!.subscription_status || 'Active'}
                    </span>
                  </div>

                  {/* Canceling message */}
                  {isCanceled && subscription!.current_period_end && (
                    <div className="p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
                      <p className="text-sm text-orange-700 dark:text-orange-400">
                        Your subscription is set to cancel. You&apos;ll have access until{' '}
                        <span className="font-medium">
                          {new Date(subscription!.current_period_end).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                          })}
                        </span>
                        .
                      </p>
                    </div>
                  )}

                  {/* Billing info */}
                  {!isCanceled && subscription!.current_period_end && (
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span>
                        Next billing date:{' '}
                        <span className="font-medium text-gray-900 dark:text-gray-100">
                          {new Date(subscription!.current_period_end).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                          })}
                        </span>
                      </span>
                    </div>
                  )}

                  {/* Manage button */}
                  <button
                    onClick={handleManageSubscription}
                    disabled={isRedirecting}
                    className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-900 dark:text-gray-100 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
                  >
                    {isRedirecting ? (
                      <>
                        <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Redirecting...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        Manage Subscription
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
