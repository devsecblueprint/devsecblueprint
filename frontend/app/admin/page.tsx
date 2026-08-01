'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { useAuth } from '@/lib/hooks/useAuth';
import { Card } from '@/components/ui/Card';
import { Spinner } from '@/components/ui/Spinner';
import { AuthGuard } from '@/components/AuthGuard';
import { ActiveSessionsModal } from '@/components/admin/ActiveSessionsModal';
import { AdminDashboardProvider, useAdminContext } from './components/AdminDashboardProvider';
import { SectionErrorBoundary } from './components/SectionErrorBoundary';
import { PlatformSummary } from './components/PlatformSummary';
import { RegistrationAnalytics } from './components/RegistrationAnalytics';
import { NeedsAttentionPanel } from './components/NeedsAttentionPanel';
import { ActivitySection } from './components/ActivitySection';
import { AdministrativeTools } from './components/AdministrativeTools';
import { DangerZone } from './components/DangerZone';

// ---------------------------------------------------------------------------
// Small wrapper to render ActiveSessionsModal from context state
// ---------------------------------------------------------------------------

function SessionsModalTrigger() {
  const { sessionsModalOpen, closeSessionsModal } = useAdminContext();
  if (!sessionsModalOpen) return null;
  return <ActiveSessionsModal onClose={closeSessionsModal} />;
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function AdminDashboardPage() {
  const router = useRouter();
  const { isAdmin, isAuthenticated, isLoading: authLoading } = useAuth();
  const [showForbidden, setShowForbidden] = useState(false);

  // Redirect non-admin users
  useEffect(() => {
    if (!authLoading && isAuthenticated && !isAdmin) {
      setShowForbidden(true);
      const timer = setTimeout(() => {
        router.push('/dashboard');
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [authLoading, isAuthenticated, isAdmin, router]);

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
          <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-10 sm:py-14">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center space-x-3 mb-2">
                <svg
                  className="w-8 h-8 text-amber-500 dark:text-amber-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                  Admin Dashboard
                </h1>
              </div>
              <p className="text-gray-600 dark:text-gray-400">
                System administration and management tools
              </p>
            </div>

            {/* Dashboard sections */}
            <AdminDashboardProvider>
              <SessionsModalTrigger />
              <div className="space-y-8">
                <SectionErrorBoundary name="Platform Summary">
                  <PlatformSummary />
                </SectionErrorBoundary>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  <div className="lg:col-span-2">
                    <SectionErrorBoundary name="Registration Analytics">
                      <RegistrationAnalytics />
                    </SectionErrorBoundary>
                  </div>
                  <SectionErrorBoundary name="Needs Attention">
                    <NeedsAttentionPanel />
                  </SectionErrorBoundary>
                </div>

                <SectionErrorBoundary name="Activity">
                  <ActivitySection />
                </SectionErrorBoundary>

                <SectionErrorBoundary name="Administrative Tools">
                  <AdministrativeTools />
                </SectionErrorBoundary>

                <SectionErrorBoundary name="Danger Zone">
                  <DangerZone />
                </SectionErrorBoundary>
              </div>
            </AdminDashboardProvider>
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
