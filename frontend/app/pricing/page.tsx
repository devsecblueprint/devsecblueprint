'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Footer } from '@/components/layout/Footer';
import { useAuth } from '@/lib/hooks/useAuth';
import { apiClient } from '@/lib/api';
import { PLANS, PlanContent } from '@/lib/data/plans';

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
  const [products, setProducts] = useState<Product[]>([]);
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);

  // Auth wall: redirect unauthenticated users to login
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login?returnTo=/pricing');
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    async function fetchProducts() {
      setIsLoading(true);
      let lastError: string | null = null;

      for (let attempt = 0; attempt < 3; attempt++) {
        const { data, error: apiError } = await apiClient.get<{ products: Product[] }>('/api/stripe/products');
        if (data?.products) {
          setProducts(data.products);
          setIsLoading(false);
          return;
        }
        lastError = apiError || 'Request failed';
        if (attempt < 2) {
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
      }

      setError('Failed to load pricing plans. Please try again later.');
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

  const handleSubscribe = async (priceId: string) => {
    setCheckoutLoading(priceId);
    const { data, error: checkoutError } = await apiClient.post<{ checkout_url: string }>(
      '/api/stripe/checkout',
      { price_id: priceId }
    );

    if (data?.checkout_url) {
      window.location.href = data.checkout_url;
    } else {
      setError(checkoutError || 'Failed to start checkout. Please try again.');
      setCheckoutLoading(null);
    }
  };

  const isCurrentPlan = (tier: string) => {
    if (!subscription) return false;
    return (
      subscription.membership_tier === tier &&
      subscription.subscription_status === 'active'
    );
  };

  const tierOrder = ['FREE', 'EXPLORER', 'BUILDER', 'BUILDER_ACADEMY'];

  const sortedProducts = [...products].sort((a, b) => {
    const aIndex = tierOrder.indexOf(a.dsb_tier);
    const bIndex = tierOrder.indexOf(b.dsb_tier);
    return aIndex - bIndex;
  });

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase(),
    }).format(price / 100);
  };

  const getPlanContent = (tier: string): PlanContent | undefined => {
    return PLANS.find(p => p.tier === tier);
  };

  const getTierBorderColor = (tier: string) => {
    switch (tier) {
      case 'FREE':
        return 'border-primary-400/30 dark:border-primary-400/20';
      case 'EXPLORER':
        return 'border-primary-400 dark:border-primary-400/60';
      case 'BUILDER':
        return 'border-amber-500 dark:border-amber-500/60';
      case 'BUILDER_ACADEMY':
        return 'border-purple-500 dark:border-purple-500/60';
      default:
        return 'border-gray-200 dark:border-gray-700';
    }
  };

  const getTierBadgeColor = (tier: string) => {
    switch (tier) {
      case 'FREE':
        return 'bg-primary-50 text-primary-700 dark:bg-primary-400/10 dark:text-primary-400';
      case 'EXPLORER':
        return 'bg-primary-50 text-primary-700 dark:bg-primary-400/15 dark:text-primary-300';
      case 'BUILDER':
        return 'bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300';
      case 'BUILDER_ACADEMY':
        return 'bg-purple-50 text-purple-700 dark:bg-purple-500/15 dark:text-purple-300';
      default:
        return 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400';
    }
  };

  const getTierButtonStyle = (tier: string) => {
    switch (tier) {
      case 'EXPLORER':
        return 'bg-primary-400 hover:bg-primary-500 text-gray-900 focus:ring-primary-400';
      case 'BUILDER':
        return 'bg-amber-500 hover:bg-amber-600 text-gray-900 focus:ring-amber-500';
      case 'BUILDER_ACADEMY':
        return 'bg-purple-500 hover:bg-purple-600 text-white focus:ring-purple-500';
      default:
        return 'bg-gray-200 hover:bg-gray-300 text-gray-800 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-200 focus:ring-gray-400';
    }
  };

  const renderPlanCard = (plan: PlanContent, product?: Product) => {
    const isFree = plan.tier === 'FREE';
    const displayPrice = isFree ? '$0' : product ? formatPrice(product.monthly_price, product.currency) : null;
    const interval = 'month';

    return (
      <div
        key={plan.tier}
        className={`bg-white dark:bg-gray-900 border-2 ${getTierBorderColor(plan.tier)} rounded-3xl p-8 lg:p-10 flex flex-col ${plan.comingSoon ? 'opacity-60 grayscale' : ''}`}
      >
        <div className="flex-1">
          {/* Tier Badge */}
          <span
            className={`inline-block px-3 py-1.5 text-xs font-semibold uppercase tracking-wide rounded-full ${getTierBadgeColor(plan.tier)} mb-5`}
          >
            {plan.tier.replace('_', ' ')}
          </span>

          {/* Plan Name */}
          <h2 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            {plan.name}
          </h2>

          {/* Tagline */}
          <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
            {plan.tagline}
          </p>

          {/* Price */}
          <div className="mb-6">
            {displayPrice ? (
              <>
                <span className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-gray-100">
                  {displayPrice}
                </span>
                <span className="text-lg text-gray-500 dark:text-gray-400 ml-2">
                  /{interval}
                </span>
              </>
            ) : (
              <div className="h-12 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            )}
          </div>

          {/* Billing Note */}
          {plan.billingNote && (
            <p className="text-sm text-gray-500 dark:text-gray-400 -mt-4 mb-6">
              {plan.billingNote}
            </p>
          )}

          {/* Description */}
          <p className="text-base text-gray-600 dark:text-gray-400 leading-relaxed mb-8">
            {plan.description}
          </p>

          {/* Included Features */}
          <div className="mb-6">
            <ul className="space-y-3" role="list" aria-label={`Features included in ${plan.name} plan`}>
              {plan.features.map((feature, idx) => (
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

          {/* Not Included Features */}
          {plan.notIncluded && plan.notIncluded.length > 0 && (
            <div className="pt-4 border-t border-gray-200 dark:border-gray-800">
              <p className="text-xs font-medium uppercase tracking-wide text-gray-400 dark:text-gray-500 mb-3">
                Not included
              </p>
              <ul className="space-y-2" role="list" aria-label={`Features not included in ${plan.name} plan`}>
                {plan.notIncluded.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <span className="flex-shrink-0 mt-0.5 text-red-300 dark:text-red-500/60" aria-hidden="true">
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </span>
                    <span className="text-sm text-gray-400 dark:text-gray-500">
                      {feature.text}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Support Boundary */}
          {plan.supportBoundary && (
            <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-800">
              <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                {plan.supportBoundary.title}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-3 leading-relaxed">
                {plan.supportBoundary.description}
              </p>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                {plan.supportBoundary.restrictionsLabel || "Restrictions:"}
              </p>
              <ul className="space-y-1.5" role="list">
                {plan.supportBoundary.restrictions.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="flex-shrink-0 mt-0.5 text-gray-400 dark:text-gray-500" aria-hidden="true">
                      •
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {item}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Disclaimer */}
          {plan.disclaimer && (
            <div className="mt-4 px-4 py-3 bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/30 rounded-lg">
              <p className="text-xs font-medium text-amber-800 dark:text-amber-300">
                {plan.disclaimer}
              </p>
            </div>
          )}
        </div>

        {/* CTA Button */}
        <div className="mt-10">
          {plan.comingSoon ? (
            <div className="w-full py-4 px-6 text-center rounded-xl bg-gray-200 dark:bg-gray-800 text-gray-500 dark:text-gray-400 font-semibold text-lg cursor-not-allowed">
              Coming Soon
            </div>
          ) : isCurrentPlan(plan.tier) ? (
            <div className="w-full py-4 px-6 text-center rounded-xl bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 font-semibold text-lg">
              Current Plan
            </div>
          ) : isFree ? (
            <div className="w-full py-4 px-6 text-center rounded-xl border-2 border-primary-400/40 text-primary-400 font-semibold text-lg">
              Default Plan
            </div>
          ) : product ? (
            <button
              onClick={() => handleSubscribe(product.price_id)}
              disabled={checkoutLoading === product.price_id}
              className={`w-full py-4 px-6 rounded-xl font-semibold text-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed ${getTierButtonStyle(plan.tier)}`}
            >
              {checkoutLoading === product.price_id ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Processing...
                </span>
              ) : (
                'Subscribe'
              )}
            </button>
          ) : (
            <div className="w-full py-4 px-6 text-center rounded-xl bg-gray-200 dark:bg-gray-800 text-gray-400 font-semibold text-lg animate-pulse">
              Loading...
            </div>
          )}
        </div>
      </div>
    );
  };

  // Show loading while checking auth
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
              Choose Your Plan
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
              Unlock exclusive Discord community access, guided walkthroughs, and premium content with a membership plan.
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

          {/* Loading State */}
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {[...Array(4)].map((_, i) => (
                <div
                  key={i}
                  className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-3xl p-8 lg:p-10 animate-pulse"
                >
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
              ))}
            </div>
          ) : (
            /* Plan Cards */
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {PLANS.map((plan) => {
                const product = sortedProducts.find(p => p.dsb_tier === plan.tier);
                return renderPlanCard(plan, product);
              })}
            </div>
          )}
        </div>
      </main>

      <Footer variant="minimal" />
    </div>
  );
}
