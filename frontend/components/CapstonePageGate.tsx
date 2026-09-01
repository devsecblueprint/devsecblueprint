'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/hooks/useAuth';
import { apiClient } from '@/lib/api';
import { CenteredSpinner } from '@/components/ui/Spinner';
import { hasBuilderAccess, SubscriptionAccessInfo } from '@/lib/entitlements';

interface CapstonePageGateProps {
  title: string;
  description: string;
  children: React.ReactNode;
}

/**
 * CapstonePageGate Component
 *
 * Wraps capstone page content and gates it behind Builder/Contributor/Admin access.
 * Free-tier users see only the title, description, and an upgrade prompt.
 * Builder, Contributor, and Admin users see the full content.
 */
export function CapstonePageGate({ title, description, children }: CapstonePageGateProps) {
  const { isAuthenticated, isAdmin } = useAuth();
  const [hasAccess, setHasAccess] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function checkAccess() {
      if (!isAuthenticated) {
        setIsLoading(false);
        return;
      }

      if (isAdmin) {
        setHasAccess(true);
        setIsLoading(false);
        return;
      }

      const { data } = await apiClient.get<SubscriptionAccessInfo>('/api/stripe/subscription');
      if (hasBuilderAccess(data)) {
        setHasAccess(true);
        setIsLoading(false);
        return;
      }

      // Check contributor role
      const profileRes = await apiClient.getUserProfile();
      if (profileRes.data?.contributor_role) {
        setHasAccess(true);
        setIsLoading(false);
        return;
      }

      setHasAccess(false);
      setIsLoading(false);
    }

    checkAccess();
  }, [isAuthenticated, isAdmin]);

  if (isLoading) {
    return (
      <div className="py-12">
        <CenteredSpinner size="lg" />
      </div>
    );
  }

  if (hasAccess) {
    return <>{children}</>;
  }

  // Locked state for Free-tier users
  return (
    <div>
      <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
        {title}
      </h1>
      <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
        {description}
      </p>

      <div className="border-t border-gray-200 dark:border-gray-800 pt-10">
        <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-8 lg:p-10 text-center max-w-lg mx-auto">
          <div className="text-4xl mb-4">🔒</div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-3">
            Capstone Project Locked
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-6 leading-relaxed">
            Capstone projects — including instructions, submission, and expert review — are available exclusively to Builder members and contributors.
          </p>
          <a
            href="/pricing"
            className="inline-block px-8 py-3.5 bg-primary-400 hover:bg-primary-500 text-gray-900 font-semibold rounded-xl transition-colors"
          >
            Upgrade to Builder
          </a>
        </div>
      </div>
    </div>
  );
}
