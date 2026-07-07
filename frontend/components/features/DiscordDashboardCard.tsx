'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { apiClient } from '@/lib/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

interface DiscordStatus {
  connected: boolean;
  discord_username?: string | null;
  discord_avatar_url?: string | null;
  platform_state?: string | null;
  last_synced_at?: string | null;
  last_sync_status?: string | null;
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
 * DiscordDashboardCard
 *
 * Displays Discord connection status on the dashboard.
 * - If not connected: shows "Connect Discord" button
 * - If connected: shows Discord icon + username
 */
export function DiscordDashboardCard() {
  const [status, setStatus] = useState<DiscordStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
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
    // Redirect to Discord OAuth start
    window.location.href = `${API_BASE_URL}/auth/discord/start`;
  };

  if (isLoading) {
    return (
      <Card padding="md">
        <div className="flex items-center justify-center py-4">
          <Spinner size="sm" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card padding="md">
        <div className="flex items-center space-x-3">
          <DiscordIcon className="w-6 h-6 text-gray-400" />
          <span className="text-sm text-gray-500 dark:text-gray-400">
            Unable to load Discord status
          </span>
        </div>
      </Card>
    );
  }

  if (status?.connected) {
    return (
      <Card padding="md">
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0 text-[#5865F2]">
            <DiscordIcon className="w-6 h-6" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
              Discord Connected
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
              {status.discord_username || 'Connected'}
            </p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card padding="md">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0 text-gray-400">
            <DiscordIcon className="w-6 h-6" />
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Connect Discord for role sync
          </p>
        </div>
        <Button variant="primary" size="sm" onClick={handleConnect}>
          Connect Discord
        </Button>
      </div>
    </Card>
  );
}
