'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Footer } from '@/components/layout/Footer';
import { useAuth } from '@/lib/hooks/useAuth';
import { apiClient } from '@/lib/api';

interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
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

  useEffect(() => {
    async function fetchProducts() {
      setIsLoading(true);
      const { data, error: apiError } = await apiClient.get<Product[]>('/api/stripe/products');
      if (apiError) {
        setError('Failed to load pricing plans. Please try again later.');
      } else if (data) {
        setProducts(data);
      }
      setIsLoading(false);
    }

    fetchProducts();
  }, []);

  useEffect(() => {
    async function fetchSubscription() {
      if (!isAuthenticated || authLoading) return;
      const { data } = await apiClient.get<SubscriptionInfo>('/api/stripe/subscription');
      if (data) {
        setSubscription(data);
      }
    }

    fetchSubscription();
  }, [isAuthenticated, authLoading]);

  const handleSubscribe = async (priceId: string) => {
    if (!isAuthenticated) {
      router.push(`/login?returnTo=/pricing`);
      return;
    }

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

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'EXPLORER':
        return 'border-blue-500 dark:border-blue-400';
      case 'BUILDER':
        return 'border-amber-500 dark:border-amber-400';
      case 'BUILDER_ACADEMY':
        return 'border-purple-500 dark:border-purple-400';
      default:
        return 'border-gray-300 dark:border-gray-700';
    }
  };

  const getTierBadgeColor = (tier: string) => {
    switch (tier) {
      case 'EXPLORER':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'BUILDER':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200';
      case 'BUILDER_ACADEMY':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
    }
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 flex flex-col">
      <NavbarWithAuth />

      <main className="flex-1 pt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              Choose Your Plan
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              Unlock exclusive Discord community access and premium content with a membership plan.
            </p>
          </div>

          {/* Error State */}
          {error && (
            <div className="mb-8 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-center">
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[...Array(4)].map((_, i) => (
                <div
                  key={i}
                  className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 animate-pulse"
                >
                  <div className="h-6 w-24 bg-gray-200 dark:bg-gray-700 rounded mb-4" />
                  <div className="h-10 w-32 bg-gray-200 dark:bg-gray-700 rounded mb-2" />
                  <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded mb-6" />
                  <div className="space-y-2">
                    <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded" />
                    <div className="h-4 w-3/4 bg-gray-200 dark:bg-gray-700 rounded" />
                  </div>
                  <div className="h-12 w-full bg-gray-200 dark:bg-gray-700 rounded-lg mt-8" />
                </div>
              ))}
            </div>
          ) : (
            /* Plan Cards */
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Free Plan Card (always shown) */}
              <div className="bg-white dark:bg-gray-900 border-2 border-gray-300 dark:border-gray-700 rounded-2xl p-6 flex flex-col">
                <div className="flex-1">
                  <span className="inline-block px-3 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 mb-4">
                    FREE
                  </span>
                  <div className="mb-6">
                    <span className="text-3xl font-bold text-gray-900 dark:text-gray-100">$0</span>
                    <span className="text-gray-500 dark:text-gray-400 ml-1">/month</span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Access free courses and community resources to start your DevSecOps journey.
                  </p>
                </div>
                <div className="mt-8">
                  {isCurrentPlan('FREE') ? (
                    <div className="w-full py-3 px-4 text-center rounded-lg bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 font-medium">
                      Current Plan
                    </div>
                  ) : (
                    <div className="w-full py-3 px-4 text-center rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 font-medium">
                      Default Plan
                    </div>
                  )}
                </div>
              </div>

              {/* Paid Plan Cards */}
              {sortedProducts
                .filter(p => p.dsb_tier !== 'FREE')
                .map((product) => (
                  <div
                    key={product.id}
                    className={`bg-white dark:bg-gray-900 border-2 ${getTierColor(product.dsb_tier)} rounded-2xl p-6 flex flex-col`}
                  >
                    <div className="flex-1">
                      <span className={`inline-block px-3 py-1 text-xs font-medium rounded-full ${getTierBadgeColor(product.dsb_tier)} mb-4`}>
                        {product.dsb_tier.replace('_', ' ')}
                      </span>
                      <div className="mb-6">
                        <span className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                          {formatPrice(product.price, product.currency)}
                        </span>
                        <span className="text-gray-500 dark:text-gray-400 ml-1">
                          /{product.interval}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {product.description || `Get access to ${product.name} features and Discord role.`}
                      </p>
                    </div>
                    <div className="mt-8">
                      {isCurrentPlan(product.dsb_tier) ? (
                        <div className="w-full py-3 px-4 text-center rounded-lg bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 font-medium">
                          Current Plan
                        </div>
                      ) : (
                        <button
                          onClick={() => handleSubscribe(product.price_id)}
                          disabled={checkoutLoading === product.price_id}
                          className="w-full py-3 px-4 rounded-lg bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {checkoutLoading === product.price_id ? (
                            <span className="flex items-center justify-center gap-2">
                              <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                              </svg>
                              Processing...
                            </span>
                          ) : (
                            'Subscribe'
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      </main>

      <Footer variant="minimal" />
    </div>
  );
}
