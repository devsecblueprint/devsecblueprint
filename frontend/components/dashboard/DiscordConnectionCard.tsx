'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { apiClient } from '@/lib/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

interface DiscordStatus {
  connected: boolean;
  discord_username: string | null;
  discord_avatar_url: string | null;
  discord_roles?: Array<{ name: string; color: string | null }>;
  platform_state: string | null;
  last_synced_at: string | null;
  last_sync_status: string | null;
}

/**
 * Discord icon SVG component (inline Discord logo)
 */
function DiscordIcon({ className = 'w-6 h-6' }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
    </svg>
  );
}

/**
 * Formats the platform_state into a human-readable status label.
 * Returns null for unknown or missing states.
 */
function formatPlatformState(platformState: string | null): string | null {
  if (!platformState) return null;
  switch (platformState) {
    case 'Roles_Synced':
      return '✓ Roles synced';
    case 'Server_Joined':
      return '✓ Server joined';
    case 'Discord_Verified':
      return '✓ Verified';
    default:
      return null;
  }
}

/**
 * DiscordConnectionCard
 *
 * Displays Discord connection status with connect/manage actions.
 * Fetches Discord status internally via apiClient.
 *
 * - Connected: shows Discord username, synced role (platform_state), sync status, disconnect button
 * - Not connected: "Connect Discord" button that redirects to OAuth flow
 * - Error: neutral "Unable to load Discord status" message
 * - Loading: spinner while fetching
 */
export function DiscordConnectionCard() {
  const [status, setStatus] = useState<DiscordStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDisconnecting, setIsDisconnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDiscordStatus();
  }, []);

  const fetchDiscordStatus = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data, error: apiError } = await apiClient.get<DiscordStatus>('/api/discord/status');
      if (apiError) {
        setError(apiError);
        return;
      }
      if (data) {
        setStatus(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch Discord status');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConnect = () => {
    window.location.href = `${API_BASE_URL}/auth/discord/start`;
  };

  const handleDisconnect = async () => {
    setIsDisconnecting(true);
    try {
      await apiClient.delete('/api/discord/disconnect');
      await fetchDiscordStatus();
    } catch (err) {
      // If disconnect fails, still re-fetch to show current state
      await fetchDiscordStatus();
    } finally {
      setIsDisconnecting(false);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <Card padding="md">
        <div className="flex items-center space-x-3 mb-4">
          <DiscordIcon className="w-6 h-6 text-[#5865F2]" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Discord</h3>
        </div>
        <div className="flex items-center justify-center py-6">
          <Spinner size="sm" />
        </div>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card padding="md">
        <div className="flex items-center space-x-3 mb-4">
          <DiscordIcon className="w-6 h-6 text-gray-400 dark:text-gray-500" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Discord</h3>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Unable to load Discord status
        </p>
      </Card>
    );
  }

  // Connected state
  if (status?.connected) {
    return (
      <Card padding="md">
        {/* Header: Discord icon + title on left, Connected badge on right */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <DiscordIcon className="w-6 h-6 text-[#5865F2]" />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Discord</h3>
          </div>
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
            Connected
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </span>
        </div>

        {/* Profile section: inner card with avatar + username + status */}
        <div className="bg-gray-100 dark:bg-gray-800 rounded-xl p-3 mb-4">
          <div className="flex items-center space-x-3">
            {status.discord_avatar_url ? (
              <img
                src={status.discord_avatar_url}
                alt={`${status.discord_username || 'Discord'} avatar`}
                className="w-10 h-10 rounded-full ring-2 ring-[#5865F2]"
              />
            ) : (
              <div className="w-10 h-10 rounded-full ring-2 ring-[#5865F2] bg-[#5865F2] flex items-center justify-center">
                <DiscordIcon className="w-5 h-5 text-white" />
              </div>
            )}
            <div className="min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                {status.discord_username || 'Connected'}
              </p>
              {formatPlatformState(status.platform_state) && (
                <p className="text-xs text-green-600 dark:text-green-400">
                  {formatPlatformState(status.platform_state)}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Roles section */}
        <div className="mb-4">
          <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
            Roles
          </p>
          <div className="flex flex-wrap gap-2">
            {status.discord_roles && status.discord_roles.length > 0 ? (
              status.discord_roles.map((role) => (
                <span
                  key={role.name}
                  className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${
                    !role.color
                      ? 'bg-gray-100 text-gray-600 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700'
                      : ''
                  }`}
                  style={{
                    backgroundColor: role.color ? `${role.color}15` : undefined,
                    color: role.color || undefined,
                    borderColor: role.color ? `${role.color}30` : undefined,
                  }}
                >
                  {role.color && (
                    <span
                      className="w-2 h-2 rounded-full mr-1.5"
                      style={{ backgroundColor: role.color }}
                      aria-hidden="true"
                    />
                  )}
                  {role.name}
                </span>
              ))
            ) : (
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400 border border-gray-200 dark:border-gray-700">
                No roles assigned
              </span>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleDisconnect}
            disabled={isDisconnecting}
            className="inline-flex items-center border border-red-200 dark:border-red-800 text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px]"
            aria-label="Disconnect Discord account"
          >
            {isDisconnecting ? 'Disconnecting...' : 'Disconnect'}
          </button>
        </div>
      </Card>
    );
  }

  // Not connected state
  return (
    <Card padding="md">
      <div className="flex items-center space-x-3 mb-4">
        <DiscordIcon className="w-6 h-6 text-gray-400 dark:text-gray-500" />
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Discord</h3>
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
        Connect your Discord account for role sync and community access.
      </p>
      <Button variant="primary" size="sm" onClick={handleConnect}>
        Connect Discord
      </Button>
    </Card>
  );
}
