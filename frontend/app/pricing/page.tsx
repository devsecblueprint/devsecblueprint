'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Footer } from '@/components/layout/Footer';
import { useAuth } from '@/lib/hooks/useAuth';
import { apiClient } from '@/lib/api';
import { BUILDER_PLAN, FREE_PLAN, SUBSCRIPTION_COMPARISONS } from '@/lib/data/plans';

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
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login?returnTo=/pricing');
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    async function fetchProducts() {
      setIsLoading(true);

      for (let attempt = 0; attempt < 3; attempt++) {
        const { data, error: apiError } = await apiClient.get<{ products: Product[] }>('/api/stripe/products');
        if (data?.products) {
          const builderProduct = data.products.find(p => p.dsb_tier === 'BUILDER');
          setProduct(builderProduct || null);
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
    if (!product) return;
    setCheckoutLoading(true);
    const { data, error: checkoutError } = await apiClient.post<{ checkout_url: string }>(
      '/api/stripe/checkout',
      { price_id: product.price_id }
    );

    if (data?.checkout_url) {
      window.location.href = data.checkout_url;
    } else {
      setError(checkoutError || 'Failed to start checkout. Please try again.');
      setCheckoutLoading(false);
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

  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-950 flex flex-col">
        <NavbarWithAuth />
        <main className="flex-1 pt-16 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin h-8 w-8 border-4 border-primary-400 border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">Loading...</p>
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
              {/* Free Plan */}
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
                  {!isCurrentPlan ? (
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

              {/* Builder Plan */}
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
                          <span className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-gray-100">
                            {formatPrice(product.monthly_price, product.currency)}
                          </span>
                          <span className="text-lg text-gray-500 dark:text-gray-400 ml-2">
                            /month
                          </span>
                        </>
                      ) : (
                        <div className="h-12 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                      )}
                    </div>

                    {/* Billing Note */}
                    {BUILDER_PLAN.billingNote && (
                      <p className="text-sm text-gray-500 dark:text-gray-400 -mt-4 mb-6">
                        {BUILDER_PLAN.billingNote}
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
                  </div>

                  {/* CTA Button */}
                  <div className="mt-10">
                    {isCurrentPlan ? (
                      <div className="w-full py-4 px-6 text-center rounded-xl bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 font-semibold text-lg">
                        Current Plan
                      </div>
                    ) : (
                      <div className="w-full py-4 px-6 text-center rounded-xl bg-gray-200 dark:bg-gray-800 text-gray-500 dark:text-gray-400 font-semibold text-lg cursor-not-allowed">
                        Coming Soon
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Comparison Section */}
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                How we compare
              </h2>
              <p className="text-lg text-gray-600 dark:text-gray-400 max-w-xl mx-auto">
                The same skills other platforms charge two to three times more for — at a price that makes sense.
              </p>
            </div>

            <div className="space-y-4">
              {SUBSCRIPTION_COMPARISONS.map((item) => {
                const isDSB = item.name.includes('DSB');
                return (
                  <div
                    key={item.name}
                    className={`flex items-center justify-between p-5 sm:p-6 rounded-2xl border-2 ${
                      isDSB
                        ? 'border-amber-500 bg-amber-50/50 dark:bg-amber-500/5 dark:border-amber-500/60'
                        : 'border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900'
                    }`}
                  >
                    <div>
                      <p className={`font-semibold text-base sm:text-lg ${
                        isDSB
                          ? 'text-gray-900 dark:text-gray-100'
                          : 'text-gray-700 dark:text-gray-300'
                      }`}>
                        {item.name}
                      </p>
                      <p className={`text-sm ${
                        isDSB
                          ? 'text-gray-600 dark:text-gray-400'
                          : 'text-gray-500 dark:text-gray-500'
                      }`}>
                        {item.description}
                      </p>
                    </div>
                    <div className="text-right ml-4">
                      <span className={`text-2xl sm:text-3xl font-bold whitespace-nowrap ${
                        isDSB
                          ? 'text-amber-500'
                          : 'text-gray-400 dark:text-gray-500'
                      }`}>
                        {item.price}
                      </span>
                      {item.priceNote && (
                        <p className={`text-xs mt-0.5 whitespace-nowrap ${
                          isDSB
                            ? 'text-amber-500/70'
                            : 'text-gray-400 dark:text-gray-500'
                        }`}>
                          {item.priceNote}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </main>

      <Footer variant="minimal" />
    </div>
  );
}
