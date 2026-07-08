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
import { useAuth } from '@/lib/hooks/useAuth';
import type { WalkthroughDetail as WalkthroughDetailType, Walkthrough } from '@/lib/types';

interface WalkthroughPageTemplateProps {
  walkthrough: Walkthrough;
  readme: string;
}

export function WalkthroughPageTemplate({ walkthrough: initialWalkthrough, readme }: WalkthroughPageTemplateProps) {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const [walkthrough, setWalkthrough] = useState<WalkthroughDetailType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [membershipTier, setMembershipTier] = useState<string>('FREE');
  const [tierLoading, setTierLoading] = useState(true);
  const [walkthroughLocked, setWalkthroughLocked] = useState(false);

  useEffect(() => {
    async function checkSubscription() {
      if (!isAuthenticated) return;
      const [subRes, tiersRes] = await Promise.all([
        apiClient.get<{ membership_tier: string }>('/api/stripe/subscription'),
        apiClient.getWalkthroughAccessTiers(),
      ]);
      if (subRes.data?.membership_tier) {
        setMembershipTier(subRes.data.membership_tier);
      }
      if (tiersRes.data?.access_tiers) {
        setWalkthroughLocked(tiersRes.data.access_tiers[initialWalkthrough.id] === 'BUILDER');
      }
      setTierLoading(false);
    }
    checkSubscription();
  }, [isAuthenticated, initialWalkthrough.id]);

  useEffect(() => {
    const loadProgress = async () => {
      try {
        setIsLoading(true);
        setError(null);

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

        // Only auto-start progress if user has access
        if (progress.status === 'not_started' && !walkthroughLocked || (walkthroughLocked && membershipTier === 'BUILDER')) {
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
        setWalkthrough({
          ...initialWalkthrough,
          readme,
          progress: { status: 'not_started' }
        });
      } finally {
        setIsLoading(false);
      }
    };

    // Wait for tier loading to complete before loading progress
    if (!tierLoading) {
      loadProgress();
    }
  }, [initialWalkthrough, readme, tierLoading, walkthroughLocked, membershipTier]);

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
        triggerBadgeCheck();
      } else {
        alert(`Failed to update progress: ${result.error}`);
      }
    } catch (err) {
      console.error('Failed to mark as complete:', err);
      alert('Failed to update progress. Please try again.');
    }
  };

  const hasAccess = !walkthroughLocked || membershipTier === 'BUILDER';

  return (
    <AuthGuard>
      <ErrorBoundary>
        <div className="min-h-screen bg-white dark:bg-gray-950">
          <NavbarWithAuth />

          <main className="pt-16">
            <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
              {(isLoading || tierLoading) && (
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

              {walkthrough && !isLoading && !tierLoading && !error && (
                <>
                  {hasAccess ? (
                    <WalkthroughDetail 
                      walkthrough={walkthrough}
                      onMarkComplete={handleMarkComplete}
                    />
                  ) : (
                    /* Free user: show only metadata + upgrade prompt */
                    <div>
                      {/* Walkthrough metadata preview */}
                      <div className="mb-8">
                        <h1 className="text-3xl lg:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                          {initialWalkthrough.title}
                        </h1>
                        <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
                          {initialWalkthrough.description}
                        </p>
                        
                        {/* Meta info */}
                        <div className="flex flex-wrap gap-3 mb-6">
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                            initialWalkthrough.difficulty === 'Beginner' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                            initialWalkthrough.difficulty === 'Intermediate' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
                            'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                          }`}>
                            {initialWalkthrough.difficulty}
                          </span>
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                            ~{initialWalkthrough.estimatedTime} min
                          </span>
                        </div>

                        {/* Topics */}
                        {initialWalkthrough.topics.length > 0 && (
                          <div className="flex flex-wrap gap-2 mb-6">
                            {initialWalkthrough.topics.map((topic) => (
                              <span key={topic} className="px-2.5 py-1 text-xs rounded-md bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                                {topic}
                              </span>
                            ))}
                          </div>
                        )}

                        {/* Authors */}
                        {initialWalkthrough.authors && initialWalkthrough.authors.length > 0 && (
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            <span className="font-medium">By: </span>
                            {initialWalkthrough.authors.map((author, i) => (
                              <span key={author.name}>
                                {author.url ? (
                                  <a href={author.url} target="_blank" rel="noopener noreferrer" className="text-primary-600 dark:text-primary-400 hover:underline">
                                    {author.name}
                                  </a>
                                ) : (
                                  author.name
                                )}
                                {i < initialWalkthrough.authors!.length - 1 && ', '}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Upgrade prompt */}
                      <div className="border-t border-gray-200 dark:border-gray-800 pt-10">
                        <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-8 lg:p-10 text-center max-w-lg mx-auto">
                          <div className="text-4xl mb-4">🔒</div>
                          <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                            Upgrade to continue
                          </h3>
                          <p className="text-sm text-gray-500 dark:text-gray-400 mb-6 leading-relaxed">
                            The full walkthrough — including step-by-step instructions, code, deployment guides, and troubleshooting playbooks — is available to Explorer members and above.
                          </p>
                          <a
                            href="/pricing"
                            className="inline-block px-8 py-3.5 bg-primary-400 hover:bg-primary-500 text-gray-900 font-semibold rounded-xl transition-colors"
                          >
                            Upgrade to Explorer
                          </a>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </main>
        </div>
      </ErrorBoundary>
    </AuthGuard>
  );
}
