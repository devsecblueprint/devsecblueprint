/**
 * Client-side wrapper for Walkthrough Detail Page
 * 
 * This component handles client-side functionality like:
 * - Authentication guard
 * - Progress tracking
 * - Mark as complete functionality
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AuthGuard } from '@/components/AuthGuard';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { WalkthroughDetail } from '@/components/WalkthroughDetail';
import { updateWalkthroughProgress } from '@/lib/walkthrough-client';
import { apiClient } from '@/lib/api';
import type { Walkthrough, WalkthroughProgress, WalkthroughDetail as WalkthroughDetailType } from '@/lib/types';

interface WalkthroughDetailClientProps {
  walkthrough: Walkthrough;
  readme: string;
}

export function WalkthroughDetailClient({ walkthrough, readme }: WalkthroughDetailClientProps) {
  const router = useRouter();
  const [progress, setProgress] = useState<WalkthroughProgress>({
    status: 'not_started',
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadProgress();
  }, [walkthrough.id]);

  const loadProgress = async () => {
    try {
      const response = await apiClient.getWalkthroughProgress(walkthrough.id);
      
      if (response.data?.progress) {
        setProgress({
          status: response.data.progress.status as 'not_started' | 'in_progress' | 'completed',
          startedAt: response.data.progress.started_at,
          completedAt: response.data.progress.completed_at,
        });
      } else {
        // Default to not_started
        setProgress({
          status: 'not_started',
        });
      }
    } catch (error) {
      console.error('Failed to load progress:', error);
      // Default to not_started if fetch fails
      setProgress({
        status: 'not_started',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleMarkComplete = async () => {
    try {
      const result = await updateWalkthroughProgress(walkthrough.id, 'completed');
      if (result.success) {
        await loadProgress(); // Reload progress
        router.push('/walkthroughs'); // Navigate back to list
      } else {
        alert(result.error || 'Failed to mark walkthrough as complete. Please try again.');
      }
    } catch (error) {
      console.error('Failed to mark walkthrough as complete:', error);
      alert('Failed to mark walkthrough as complete. Please try again.');
    }
  };

  // Combine walkthrough data with readme and progress
  const walkthroughDetail: WalkthroughDetailType = {
    ...walkthrough,
    readme,
    progress,
  };

  if (isLoading) {
    return (
      <AuthGuard>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
          <NavbarWithAuth />
          <main className="pt-16">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-400"></div>
                  <p className="mt-4 text-gray-600 dark:text-gray-400">Loading walkthrough...</p>
                </div>
              </div>
            </div>
          </main>
        </div>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
        <NavbarWithAuth />
        <main className="pt-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <WalkthroughDetail
              walkthrough={walkthroughDetail}
              onMarkComplete={handleMarkComplete}
            />
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
