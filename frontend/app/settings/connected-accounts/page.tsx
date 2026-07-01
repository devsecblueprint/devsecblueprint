'use client';

import { useState, useEffect, Suspense, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { AuthGuard } from '@/components/AuthGuard';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { apiClient } from '@/lib/api';

/**
 * Discord connection status response from GET /api/discord/status
 */
interface DiscordStatus {
  connected: boolean;
  discord_username: string | null;
  discord_avatar_url: string | null;
  discord_display_name?: string | null;
  platform_state: string | null;
  last_synced_at: string | null;
  last_sync_status: string | null;
  cleanup_status?: string | null;
}

/**
 * Platform state progression steps
 */
const PLATFORM_STATES = [
  { key: 'Discord_Connected', label: 'Connected' },
  { key: 'Discord_Verified', label: 'Verified' },
  { key: 'Server_Joined', label: 'Server Joined' },
  { key: 'Roles_Synced', label: 'Roles Synced' },
];

/**
 * Get the index of the current platform state in the progression
 */
function getPlatformStateIndex(state: string | null): number {
  if (!state) return -1;
  return PLATFORM_STATES.findIndex((s) => s.key === state);
}

/**
 * Discord icon SVG component
 */
function DiscordIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
    </svg>
  );
}

/**
 * Connected Accounts page content (uses useSearchParams)
 */
function ConnectedAccountsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [discordStatus, setDiscordStatus] = useState<DiscordStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showDisconnectDialog, setShowDisconnectDialog] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [isDisconnecting, setIsDisconnecting] = useState(false);

  const fetchDiscordStatus = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    const { data, error: apiError } = await apiClient.get<DiscordStatus>('/api/discord/status');
    if (apiError) {
      setError(apiError);
    } else if (data) {
      setDiscordStatus(data);
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    fetchDiscordStatus();
  }, [fetchDiscordStatus]);

  // Handle ?discord=pending query param to show confirmation modal
  useEffect(() => {
    if (searchParams.get('discord') === 'pending') {
      setShowConfirmModal(true);
    }
  }, [searchParams]);

  const handleConnectDiscord = () => {
    // Redirect to Discord OAuth start endpoint
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || '';
    window.location.href = `${apiBaseUrl}/auth/discord/start`;
  };

  const handleConfirmIdentity = async () => {
    setIsConfirming(true);
    const { data, error: confirmError } = await apiClient.post<DiscordStatus>('/api/discord/confirm', {});
    if (confirmError) {
      setError(confirmError);
    } else if (data) {
      setDiscordStatus(data);
    }
    setShowConfirmModal(false);
    setIsConfirming(false);
    // Remove the query param
    router.replace('/settings/connected-accounts');
    // Refetch status
    await fetchDiscordStatus();
  };

  const handleDisconnectAndChooseAnother = async () => {
    setIsDisconnecting(true);
    const { error: disconnectError } = await apiClient.delete('/api/discord/disconnect');
    if (disconnectError) {
      setError(disconnectError);
    }
    setShowConfirmModal(false);
    setIsDisconnecting(false);
    router.replace('/settings/connected-accounts');
    await fetchDiscordStatus();
  };

  const handleDisconnect = async () => {
    setIsDisconnecting(true);
    const { error: disconnectError } = await apiClient.delete('/api/discord/disconnect');
    if (disconnectError) {
      setError(disconnectError);
    }
    setShowDisconnectDialog(false);
    setIsDisconnecting(false);
    await fetchDiscordStatus();
  };

  const currentStateIndex = getPlatformStateIndex(discordStatus?.platform_state ?? null);

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      <NavbarWithAuth />
      <main className="pt-16">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Connected Accounts
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-8">
            Manage external accounts linked to your DSB profile.
          </p>

          {/* Error Banner */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
            </div>
          )}

          {/* Discord Card */}
          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <DiscordIcon className="w-8 h-8 text-[#5865F2]" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Discord</h2>
            </div>

            {isLoading ? (
              /* Loading skeleton */
              <div className="animate-pulse space-y-3">
                <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-48" />
                <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-32" />
              </div>
            ) : discordStatus?.connected ? (
              /* Connected state */
              <div className="space-y-4">
                {/* User info */}
                <div className="flex items-center gap-4">
                  {discordStatus.discord_avatar_url ? (
                    <img
                      src={discordStatus.discord_avatar_url}
                      alt="Discord avatar"
                      className="w-12 h-12 rounded-full border-2 border-gray-200 dark:border-gray-700"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-full bg-[#5865F2] flex items-center justify-center">
                      <DiscordIcon className="w-6 h-6 text-white" />
                    </div>
                  )}
                  <div>
                    <p className="font-medium text-gray-900 dark:text-gray-100">
                      {discordStatus.discord_username || 'Unknown User'}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Status: {discordStatus.platform_state?.replace(/_/g, ' ') || 'Connected'}
                    </p>
                  </div>
                </div>

                {/* Platform State Progression */}
                <div className="mt-4">
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Integration Progress
                  </p>
                  <div className="flex items-center gap-1">
                    {PLATFORM_STATES.map((step, index) => (
                      <div key={step.key} className="flex items-center flex-1">
                        <div className="flex flex-col items-center flex-1">
                          <div
                            className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                              index <= currentStateIndex
                                ? 'bg-green-500 text-white'
                                : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                            }`}
                          >
                            {index <= currentStateIndex ? (
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                              </svg>
                            ) : (
                              index + 1
                            )}
                          </div>
                          <span className="text-xs text-gray-500 dark:text-gray-400 mt-1 text-center">
                            {step.label}
                          </span>
                        </div>
                        {index < PLATFORM_STATES.length - 1 && (
                          <div
                            className={`h-0.5 flex-1 mx-1 ${
                              index < currentStateIndex
                                ? 'bg-green-500'
                                : 'bg-gray-200 dark:bg-gray-700'
                            }`}
                          />
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Cleanup status indicator */}
                {discordStatus.cleanup_status && discordStatus.cleanup_status !== 'completed' && (
                  <div className="mt-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                    <p className="text-sm text-yellow-700 dark:text-yellow-400">
                      {discordStatus.cleanup_status === 'pending'
                        ? 'Role cleanup is in progress...'
                        : 'Role cleanup failed. Please contact support if roles remain on your Discord account.'}
                    </p>
                  </div>
                )}

                {/* Sync info */}
                {discordStatus.last_synced_at && (
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Last synced: {new Date(discordStatus.last_synced_at).toLocaleString()}
                    {discordStatus.last_sync_status && ` (${discordStatus.last_sync_status})`}
                  </p>
                )}

                {/* Disconnect button */}
                <button
                  onClick={() => setShowDisconnectDialog(true)}
                  className="mt-4 px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
                >
                  Disconnect Discord
                </button>
              </div>
            ) : (
              /* Not connected state */
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  Connect your Discord account to sync your membership role and join the community server.
                </p>
                <button
                  onClick={handleConnectDiscord}
                  className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-[#5865F2] rounded-lg hover:bg-[#4752C4] transition-colors focus:outline-none focus:ring-2 focus:ring-[#5865F2] focus:ring-offset-2 dark:focus:ring-offset-gray-950"
                >
                  <DiscordIcon className="w-4 h-4" />
                  Connect Discord
                </button>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Identity Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Confirm Discord Account
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Is this the Discord account you want to link?
            </p>

            {/* Show pending Discord info from status if available */}
            <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg mb-6">
              {discordStatus?.discord_avatar_url ? (
                <img
                  src={discordStatus.discord_avatar_url}
                  alt="Discord avatar"
                  className="w-10 h-10 rounded-full"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-[#5865F2] flex items-center justify-center">
                  <DiscordIcon className="w-5 h-5 text-white" />
                </div>
              )}
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  {discordStatus?.discord_username || 'Discord User'}
                </p>
                {discordStatus?.discord_display_name && (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {discordStatus.discord_display_name}
                  </p>
                )}
              </div>
            </div>

            <div className="flex flex-col gap-3">
              <button
                onClick={handleConfirmIdentity}
                disabled={isConfirming}
                className="w-full px-4 py-2.5 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
              >
                {isConfirming ? 'Confirming...' : 'Yes, this is my account'}
              </button>
              <button
                onClick={handleDisconnectAndChooseAnother}
                disabled={isDisconnecting}
                className="w-full px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
              >
                {isDisconnecting ? 'Disconnecting...' : 'Disconnect & Choose Another'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Disconnect Confirmation Dialog */}
      {showDisconnectDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-xl max-w-sm w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Disconnect Discord?
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              This will remove your managed Discord roles and stop role synchronization.
              Your subscription will not be affected.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDisconnectDialog(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
              >
                Cancel
              </button>
              <button
                onClick={handleDisconnect}
                disabled={isDisconnecting}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
              >
                {isDisconnecting ? 'Disconnecting...' : 'Disconnect'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Connected Accounts Settings Page
 * 
 * Manages Discord account connection for membership role synchronization.
 * Handles the full lifecycle: connect, confirm, view status, and disconnect.
 */
export default function ConnectedAccountsPage() {
  return (
    <AuthGuard>
      <Suspense
        fallback={
          <div className="min-h-screen flex items-center justify-center bg-white dark:bg-gray-950">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-400" />
              <p className="mt-4 text-gray-600 dark:text-gray-400">Loading...</p>
            </div>
          </div>
        }
      >
        <ConnectedAccountsContent />
      </Suspense>
    </AuthGuard>
  );
}
