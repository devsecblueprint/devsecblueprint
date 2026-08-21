'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Footer } from '@/components/layout/Footer';
import { useAuth } from '@/lib/hooks/useAuth';
import { apiClient } from '@/lib/api';
import { BUILDER_PLAN, FREE_PLAN } from '@/lib/data/plans';
import { POLICY_LINKS } from '@/lib/data/policies';

interface Product {
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

interface SubscriptionInfo {
  membership_tier: string;
  subscription_status: string | null;
  current_period_end: string | null;
  stripe_subscription_id: string | null;
}

export default function PricingPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [product, setProduct] = useState<Product | null>(null);
  const [annualProduct, setAnnualProduct] = useState<Product | null>(null);
  const [billingInterval, setBillingInterval] = useState<'month' | 'year'>('month');
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  useEffect(() => {
    async function fetchProducts() {
      setIsLoading(true);

      for (let attempt = 0; attempt < 3; attempt++) {
        const { data, error: apiError } = await apiClient.get<{ products: Product[] }>('/api/stripe/products');
        if (data?.products) {
          const builderProducts = data.products.filter(p => p.dsb_tier === 'BUILDER');
          const monthly = builderProducts.find(p => p.interval === 'month') || null;
          const annual = builderProducts.find(p => p.interval === 'year') || null;
          setProduct(monthly);
          setAnnualProduct(annual);
          setIsLoading(false);
          return;
        }
        if (attempt < 2) {
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
      }

      setError('Failed to load pricing. Please try again later.');
      setIsLoading(false);
    }

    fetchProducts();
  }, []);

  useEffect(() => {
    async function fetchSubscription() {
      if (!isAuthenticated || authLoading) return;
      for (let attempt = 0; attempt < 3; attempt++) {
        const { data } = await apiClient.get<SubscriptionInfo>('/api/stripe/subscription');
        if (data) {
          setSubscription(data);
          return;
        }
        if (attempt < 2) {
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
      }
    }

    fetchSubscription();
  }, [isAuthenticated, authLoading]);

  const handleSubscribe = async () => {
    const selectedProduct = billingInterval === 'year' ? annualProduct : product;
    if (!selectedProduct) return;

    // If not authenticated, redirect to login first
    if (!isAuthenticated) {
      router.push('/login?returnTo=/pricing');
      return;
    }

    setCheckoutLoading(true);
    const { data, error: checkoutError } = await apiClient.post<{ checkout_url: string }>(
      '/api/stripe/checkout',
      { price_id: selectedProduct.price_id }
    );

    if (data?.checkout_url) {
      window.location.href = data.checkout_url;
    } else {
      setError(checkoutError || 'Failed to start checkout. Please try again.');
      setCheckoutLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    const { data, error: portalError } = await apiClient.post<{ portal_url: string }>(
      '/api/stripe/portal',
      {}
    );

    if (data?.portal_url) {
      window.location.href = data.portal_url;
    } else {
      setError(portalError || 'Failed to open subscription management. Please try again.');
    }
  };

  const isCurrentPlan =
    subscription?.membership_tier === 'BUILDER' &&
    subscription?.subscription_status === 'active';

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase(),
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price / 100);
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 flex flex-col">
      <NavbarWithAuth />

      <main className="flex-1 pt-16">
        <div className="max-w-screen-xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20">
          {/* Header */}
          <div className="text-center mb-16">
            <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 dark:text-gray-100 mb-5">
              Builder Membership
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
              Unlock the full DSB experience — guided walkthroughs, structured tracks, group office hours, and a community of builders shipping real DevSecOps projects.
            </p>
          </div>

          {/* Error State */}
          {error && (
            <div className="mb-10 p-5 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-center">
              <p className="text-red-700 dark:text-red-300">{error}</p>
              <button
                onClick={() => setError(null)}
                className="mt-2 text-sm text-red-600 dark:text-red-400 underline hover:no-underline"
              >
                Dismiss
              </button>
            </div>
          )}

          {/* Plan Cards */}
          <div className="max-w-5xl mx-auto mb-20">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Builder Plan — Primary */}
              {isLoading ? (
                <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-3xl p-8 lg:p-10 animate-pulse">
                  <div className="h-7 w-28 bg-gray-200 dark:bg-gray-700 rounded-full mb-5" />
                  <div className="h-9 w-40 bg-gray-200 dark:bg-gray-700 rounded mb-2" />
                  <div className="h-5 w-64 bg-gray-200 dark:bg-gray-700 rounded mb-6" />
                  <div className="h-14 w-36 bg-gray-200 dark:bg-gray-700 rounded mb-6" />
                  <div className="space-y-3">
                    <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded" />
                    <div className="h-4 w-5/6 bg-gray-200 dark:bg-gray-700 rounded" />
                    <div className="h-4 w-3/4 bg-gray-200 dark:bg-gray-700 rounded" />
                  </div>
                  <div className="h-14 w-full bg-gray-200 dark:bg-gray-700 rounded-xl mt-10" />
                </div>
              ) : (
                <div className="bg-white dark:bg-gray-900 border-2 border-amber-500 dark:border-amber-500/60 rounded-3xl p-8 lg:p-10 flex flex-col">
                  <div className="flex-1">
                    {/* Tier Badge */}
                    <span className="inline-block px-3 py-1.5 text-xs font-semibold uppercase tracking-wide rounded-full bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300 mb-5">
                      Builder
                    </span>

                    {/* Plan Name */}
                    <h2 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                      {BUILDER_PLAN.name}
                    </h2>

                    {/* Tagline */}
                    <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
                      {BUILDER_PLAN.tagline}
                    </p>

                    {/* Price */}
                    <div className="mb-6">
                      {product ? (
                        <>
                          {/* Billing interval toggle */}
                          {annualProduct && (
                            <div className="flex items-center gap-3 mb-4">
                              <button
                                onClick={() => setBillingInterval('month')}
                                className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                                  billingInterval === 'month'
                                    ? 'bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-300'
                                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                                }`}
                              >
                                Monthly
                              </button>
                              <button
                                onClick={() => setBillingInterval('year')}
                                className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                                  billingInterval === 'year'
                                    ? 'bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-300'
                                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                                }`}
                              >
                                Annual
                                <span className="ml-1.5 text-xs font-semibold text-green-600 dark:text-green-400">Save 17%</span>
                              </button>
                            </div>
                          )}

                          {billingInterval === 'year' && annualProduct ? (
                            <>
                              <span className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-gray-100">
                                {formatPrice(annualProduct.price, annualProduct.currency)}
                              </span>
                              <span className="text-lg text-gray-500 dark:text-gray-400 ml-2">
                                /year
                              </span>
                              <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                                {formatPrice(annualProduct.monthly_price, annualProduct.currency)}/mo equivalent
                              </div>
                            </>
                          ) : (
                            <>
                              <span className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-gray-100">
                                {formatPrice(product.monthly_price, product.currency)}
                              </span>
                              <span className="text-lg text-gray-500 dark:text-gray-400 ml-2">
                                /month
                              </span>
                            </>
                          )}
                        </>
                      ) : (
                        <div className="h-12 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                      )}
                    </div>

                    {/* Billing Note */}
                    {BUILDER_PLAN.billingNote && (
                      <p className="text-sm text-gray-500 dark:text-gray-400 -mt-4 mb-6">
                        {billingInterval === 'year' ? 'Billed annually. Cancel anytime.' : BUILDER_PLAN.billingNote}
                      </p>
                    )}

                    {/* Description */}
                    <p className="text-base text-gray-600 dark:text-gray-400 leading-relaxed mb-8">
                      {BUILDER_PLAN.description}
                    </p>

                    {/* Included Features */}
                    <div className="mb-6">
                      <ul className="space-y-3" role="list" aria-label="Features included in Builder plan">
                        {BUILDER_PLAN.features.map((feature, idx) => (
                          <li key={idx} className="flex items-start gap-3">
                            <span className="flex-shrink-0 mt-0.5 text-green-500 dark:text-green-400" aria-hidden="true">
                              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                <path
                                  fillRule="evenodd"
                                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                  clipRule="evenodd"
                                />
                              </svg>
                            </span>
                            <span className="text-sm lg:text-base text-gray-700 dark:text-gray-300">
                              {feature.text}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Disclaimer */}
                    {BUILDER_PLAN.disclaimer && (
                      <div className="mt-4 px-4 py-3 bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/30 rounded-lg">
                        <p className="text-xs font-medium text-amber-800 dark:text-amber-300">
                          {BUILDER_PLAN.disclaimer}
                        </p>
                      </div>
                    )}

                    {/* Policy Links */}
                    <p className="mt-4 text-xs text-gray-500 dark:text-gray-400">
                      By subscribing, you agree to our{' '}
                      {POLICY_LINKS.filter(p => p.label !== 'Content and IP Sharing Policy').map((policy, idx, arr) => (
                        <span key={policy.label}>
                          <a
                            href={policy.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="underline hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                          >
                            {policy.label}
                          </a>
                          {idx < arr.length - 1 ? ', ' : '.'}
                        </span>
                      ))}
                    </p>
                  </div>

                  {/* CTA Button */}
                  <div className="mt-10">
                    {isCurrentPlan ? (
                      <div className="space-y-3">
                        <div className="w-full py-4 px-6 text-center rounded-xl bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 font-semibold text-lg">
                          Current Plan
                        </div>
                        {annualProduct && billingInterval === 'year' && (
                          <button
                            onClick={handleManageSubscription}
                            className="w-full py-3 px-6 text-center rounded-xl border-2 border-amber-500 text-amber-600 dark:text-amber-400 font-semibold text-sm hover:bg-amber-50 dark:hover:bg-amber-900/20 transition-colors"
                          >
                            Switch to Annual & Save
                          </button>
                        )}
                      </div>
                    ) : (
                      <button
                        onClick={handleSubscribe}
                        disabled={checkoutLoading || !product}
                        className="w-full py-4 px-6 text-center rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-semibold text-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {checkoutLoading ? 'Redirecting to checkout...' : (isAuthenticated ? 'Subscribe Now' : 'Sign In to Subscribe')}
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Free Plan — Entry-level */}
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-3xl p-8 lg:p-10 flex flex-col">
                <div className="flex-1">
                  {/* Tier Badge */}
                  <span className="inline-block px-3 py-1.5 text-xs font-semibold uppercase tracking-wide rounded-full bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400 mb-5">
                    Free
                  </span>

                  {/* Plan Name */}
                  <h2 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                    {FREE_PLAN.name}
                  </h2>

                  {/* Tagline */}
                  <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
                    {FREE_PLAN.tagline}
                  </p>

                  {/* Price */}
                  <div className="mb-6">
                    <span className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-gray-100">
                      $0
                    </span>
                    <span className="text-lg text-gray-500 dark:text-gray-400 ml-2">
                      /forever
                    </span>
                  </div>

                  {/* Description */}
                  <p className="text-base text-gray-600 dark:text-gray-400 leading-relaxed mb-8">
                    {FREE_PLAN.description}
                  </p>

                  {/* Included Features */}
                  <ul className="space-y-3" role="list" aria-label="Features included in Free plan">
                    {FREE_PLAN.features.map((feature, idx) => (
                      <li key={idx} className="flex items-start gap-3">
                        <span className="flex-shrink-0 mt-0.5 text-green-500 dark:text-green-400" aria-hidden="true">
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path
                              fillRule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                        </span>
                        <span className="text-sm lg:text-base text-gray-700 dark:text-gray-300">
                          {feature.text}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* CTA */}
                <div className="mt-10">
                  {!isAuthenticated ? (
                    <a
                      href="/login?returnTo=/dashboard"
                      className="block w-full py-4 px-6 text-center rounded-xl bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 font-semibold text-lg hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors"
                    >
                      Sign Up Free
                    </a>
                  ) : !isCurrentPlan ? (
                    <div className="w-full py-4 px-6 text-center rounded-xl bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 font-semibold text-lg">
                      Current Plan
                    </div>
                  ) : (
                    <div className="w-full py-4 px-6 text-center rounded-xl bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 font-medium text-lg">
                      Free Forever
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Why Builder Is Different */}
          <div className="max-w-4xl mx-auto mb-20">
            <div className="text-center mb-12">
              <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-5">
                Why Builder Is Different
              </h2>
              <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto leading-relaxed">
                Most platforms give you more content. Builder gives you a reason to use what you learn.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Card 1 — Learn With Structure */}
              <div className="p-6 sm:p-8 rounded-2xl bg-gray-50 dark:bg-gray-900/60 border border-gray-200 dark:border-gray-800">
                <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-500/15 flex items-center justify-center mb-4">
                  <svg className="w-5 h-5 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">
                  Learn With Structure
                </h3>
                <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 leading-relaxed">
                  Follow focused DevSecOps and Cloud Security pathways instead of trying to figure out what to study next.
                </p>
              </div>

              {/* Card 2 — Build Real Systems */}
              <div className="p-6 sm:p-8 rounded-2xl bg-gray-50 dark:bg-gray-900/60 border border-gray-200 dark:border-gray-800">
                <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-500/15 flex items-center justify-center mb-4">
                  <svg className="w-5 h-5 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">
                  Build Real Systems
                </h3>
                <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 leading-relaxed">
                  Work through engineering problems, walkthroughs, and capstones based on the kind of work practitioners actually do.
                </p>
              </div>

              {/* Card 3 — Get Feedback */}
              <div className="p-6 sm:p-8 rounded-2xl bg-gray-50 dark:bg-gray-900/60 border border-gray-200 dark:border-gray-800">
                <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-500/15 flex items-center justify-center mb-4">
                  <svg className="w-5 h-5 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">
                  Get Feedback
                </h3>
                <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 leading-relaxed">
                  Submit eligible work for review, ask questions during Office Hours, and learn alongside experienced practitioners.
                </p>
              </div>

              {/* Card 4 — Keep Moving */}
              <div className="p-6 sm:p-8 rounded-2xl bg-gray-50 dark:bg-gray-900/60 border border-gray-200 dark:border-gray-800">
                <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-500/15 flex items-center justify-center mb-4">
                  <svg className="w-5 h-5 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">
                  Keep Moving
                </h3>
                <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 leading-relaxed">
                  Builder Sessions, community accountability, and continuously released content give you a reason to keep building instead of collecting unfinished courses.
                </p>
              </div>
            </div>

            {/* Social proof bridge */}
            <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-10">
              The work works.{' '}
              <a href="/" className="font-medium text-amber-600 dark:text-amber-400 hover:underline">
                See what DSB members have accomplished.
              </a>
            </p>

            {/* Pricing + CTA */}
            <div className="text-center mt-10">
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-6">
                $29.99/month. Cancel anytime.
              </p>
              {!isCurrentPlan && (
                <button
                  onClick={handleSubscribe}
                  disabled={checkoutLoading || !product}
                  className="inline-block px-8 py-4 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-semibold text-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {checkoutLoading ? 'Redirecting to checkout...' : (isAuthenticated ? 'Join Builder' : 'Sign In to Join Builder')}
                </button>
              )}
            </div>
          </div>

          {/* Have Questions? */}
          <div className="max-w-xl mx-auto text-center border-t border-gray-200 dark:border-gray-800 pt-12">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-3">
              Not sure if Builder is right for you?
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Email{' '}
              <a
                href="mailto:community@devsecblueprint.com"
                className="font-medium text-amber-600 dark:text-amber-400 hover:underline"
              >
                community@devsecblueprint.com
              </a>
              {' '}with any questions about membership, curriculum, community access, or getting started.
            </p>
          </div>

        </div>
      </main>

      <Footer variant="minimal" />
    </div>
  );
}
