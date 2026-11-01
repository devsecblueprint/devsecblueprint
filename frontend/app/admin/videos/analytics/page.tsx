/**
 * Admin Video Analytics Page
 *
 * Aggregate view of how members watch the Video Library.
 * Admin only, same auth and 403 handling as /admin/videos.
 */

'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { AuthGuard } from '@/components/AuthGuard';
import { useAuth } from '@/lib/hooks/useAuth';
import { Card } from '@/components/ui/Card';
import { Spinner } from '@/components/ui/Spinner';
import { VideoAnalytics } from '@/components/admin/VideoAnalytics';

export default function AdminVideoAnalyticsPage() {
  const router = useRouter();
  const { isAdmin, isAuthenticated, isLoading: authLoading } = useAuth();
  const showForbidden = !authLoading && isAuthenticated && !isAdmin;

  // Redirect non-admin users after showing the 403 screen
  useEffect(() => {
    if (showForbidden) {
      const timer = setTimeout(() => {
        router.push('/dashboard');
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [showForbidden, router]);

  // Loading while checking auth
  if (authLoading && !isAdmin) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-950 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  // Forbidden screen for authenticated non-admin users
  if (showForbidden) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-950">
        <NavbarWithAuth />
        <main className="pt-16 flex items-center justify-center min-h-[calc(100vh-4rem)]">
          <div className="max-w-md mx-auto px-4">
            <Card padding="lg">
              <div className="text-center py-8">
                <div className="mb-6">
                  <svg
                    className="w-20 h-20 mx-auto text-red-500 dark:text-red-400"
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
                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                  403 - Access Denied
                </h1>
                <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
                  You don&apos;t have permission to access this page. Admin access is required.
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-500 mb-6">
                  Redirecting to dashboard...
                </p>
                <Spinner size="md" />
              </div>
            </Card>
          </div>
        </main>
      </div>
    );
  }

  // Non-admin unauthenticated returns null
  if (!isAdmin) {
    return null;
  }

  return (
    <AuthGuard>
      <div className="min-h-screen bg-white dark:bg-gray-950">
        <NavbarWithAuth />
        <main className="pt-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Link
              href="/admin/videos"
              className="inline-flex items-center min-h-[44px] text-sm font-medium text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 mb-2"
            >
              &larr; Back to Videos
            </Link>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              Video Analytics
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1 mb-8">
              How members watch the Video Library
            </p>
            <VideoAnalytics />
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
