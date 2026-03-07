/**
 * Walkthroughs Browser Page
 * 
 * Displays all available walkthroughs with filtering and search capabilities.
 * Protected by authentication - redirects to home if not logged in.
 * 
 * Walkthroughs are loaded from local content (frontend/content/walkthroughs/)
 * Progress data is fetched from backend API
 * 
 * Requirements: 4.1, 4.2, 4.3, 4.4, 5.1
 */

'use client';

import { useEffect, useState } from 'react';
import { AuthGuard } from '@/components/AuthGuard';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { WalkthroughBrowser } from '@/components/WalkthroughBrowser';
import { getWalkthroughsWithProgress } from '@/lib/walkthrough-client';
import type { WalkthroughWithProgress } from '@/lib/types';

export default function WalkthroughsPage() {
  const [walkthroughs, setWalkthroughs] = useState<WalkthroughWithProgress[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadWalkthroughs();
  }, []);

  const loadWalkthroughs = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Load walkthroughs from local content with progress data from backend
      const walkthroughsData = await getWalkthroughsWithProgress();
      setWalkthroughs(walkthroughsData);
    } catch (err) {
      console.error('Failed to load walkthroughs:', err);
      setError(err instanceof Error ? err.message : 'Failed to load walkthroughs');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthGuard>
      <ErrorBoundary>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
          <NavbarWithAuth />
          
          <main className="pt-16">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              {isLoading ? (
                <div className="flex items-center justify-center min-h-[400px]">
                  <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-400"></div>
                    <p className="mt-4 text-gray-600 dark:text-gray-400">Loading walkthroughs...</p>
                  </div>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center min-h-[400px]">
                  <div className="text-center max-w-md">
                    <div className="text-red-500 dark:text-red-400 mb-4">
                      <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                      Unable to Load Walkthroughs
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400 mb-6">
                      {error}
                    </p>
                    <button
                      onClick={loadWalkthroughs}
                      className="px-6 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
                    >
                      Try Again
                    </button>
                  </div>
                </div>
              ) : (
                <WalkthroughBrowser initialWalkthroughs={walkthroughs} />
              )}
            </div>
          </main>
        </div>
      </ErrorBoundary>
    </AuthGuard>
  );
}
