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
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
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
                    d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
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

              <SectionErrorBoundary name="Platform Summary">
                <PlatformSummary />
              </SectionErrorBoundary>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
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
            </AdminDashboardProvider>
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
