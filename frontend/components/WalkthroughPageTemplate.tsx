'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AuthGuard } from '@/components/AuthGuard';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { Card } from '@/components/ui/Card';
import { CenteredSpinner } from '@/components/ui/Spinner';
import { WalkthroughDetail } from '@/components/WalkthroughDetail';
import { apiClient } from '@/lib/api';
import { triggerBadgeCheck } from '@/lib/events';
import type { WalkthroughDetail as WalkthroughDetailType, Walkthrough } from '@/lib/types';

interface WalkthroughPageTemplateProps {
  walkthrough: Walkthrough;
  readme: string;
}

export function WalkthroughPageTemplate({ walkthrough: initialWalkthrough, readme }: WalkthroughPageTemplateProps) {
  const router = useRouter();
  const [walkthrough, setWalkthrough] = useState<WalkthroughDetailType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProgress = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Get progress from backend
        const response = await apiClient.getWalkthroughProgress(initialWalkthrough.id);
        
        const progress = response.data?.progress
          ? {
              status: response.data.progress.status as 'not_started' | 'in_progress' | 'completed',
              startedAt: response.data.progress.started_at,
              completedAt: response.data.progress.completed_at
            }
          : { status: 'not_started' as const };

        setWalkthrough({
          ...initialWalkthrough,
          readme,
          progress
        });

        // Mark as in_progress on first view
        if (progress.status === 'not_started') {
          try {
            const result = await apiClient.updateWalkthroughProgress(initialWalkthrough.id, 'in_progress');
            if (result.data) {
              setWalkthrough(prev => prev ? {
                ...prev,
                progress: {
                  ...prev.progress,
                  status: 'in_progress',
                  startedAt: new Date().toISOString()
                }
              } : null);
            }
          } catch (progressError) {
            console.error('Failed to update progress:', progressError);
          }
        }
      } catch (err) {
        console.error('Error loading progress:', err);
        // Still show the walkthrough even if progress fails
        setWalkthrough({
          ...initialWalkthrough,
          readme,
          progress: { status: 'not_started' }
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadProgress();
  }, [initialWalkthrough, readme]);

  const handleMarkComplete = async () => {
    if (!walkthrough) return;

    try {
      const result = await apiClient.updateWalkthroughProgress(initialWalkthrough.id, 'completed');
      if (result.data) {
        setWalkthrough({
          ...walkthrough,
          progress: {
            ...walkthrough.progress,
            status: 'completed',
            completedAt: new Date().toISOString()
          }
        });
        // Trigger badge check after completing a walkthrough
        triggerBadgeCheck();
      } else {
        alert(`Failed to update progress: ${result.error}`);
      }
    } catch (err) {
      console.error('Failed to mark as complete:', err);
      alert('Failed to update progress. Please try again.');
    }
  };

  return (
    <AuthGuard>
      <ErrorBoundary>
        <div className="min-h-screen bg-white dark:bg-gray-950">
          <NavbarWithAuth />

          <main className="pt-16">
            <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
              {isLoading && (
                <CenteredSpinner size="lg" />
              )}

              {error && !isLoading && (
                <Card padding="lg">
                  <div className="text-center py-12">
                    <div className="mb-6">
                      <svg 
                        className="w-16 h-16 mx-auto text-red-500 dark:text-red-400" 
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path 
                          strokeLinecap="round" 
                          strokeLinejoin="round" 
                          strokeWidth={2} 
                          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
                        />
                      </svg>
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                      Error Loading Walkthrough
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400 mb-6">
                      We encountered an error while loading this walkthrough.
                    </p>
                    <button
                      onClick={() => router.push('/walkthroughs')}
                      className="inline-flex items-center px-6 py-3 bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors"
                    >
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                      </svg>
                      Back to Walkthroughs
                    </button>
                  </div>
                </Card>
              )}

              {walkthrough && !isLoading && !error && (
                <WalkthroughDetail 
                  walkthrough={walkthrough}
                  onMarkComplete={handleMarkComplete}
                />
              )}
            </div>
          </main>
        </div>
      </ErrorBoundary>
    </AuthGuard>
  );
}
