'use client';

import { useEffect, useState, useCallback } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { apiClient } from '@/lib/api';

interface AdminDiscordUserInfo {
  discord_username?: string | null;
  discord_user_id?: string | null;
  connection_status?: string | null;
  verification_status?: string | null;
  guild_membership_status?: string | null;
  membership_tier?: string | null;
  current_discord_role?: string | null;
  stripe_subscription_status?: string | null;
  last_synced_at?: string | null;
}

interface AuditEntry {
  event_type: string;
  timestamp: string;
  actor?: string | null;
  details?: string | null;
  reason?: string | null;
}

/**
 * Discord icon SVG
 */
function DiscordIcon({ className = 'w-5 h-5' }: { className?: string }) {
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

interface AdminUserDiscordPanelProps {
  userId: string;
}

/**
 * AdminUserDiscordPanel
 *
 * Admin panel for viewing and managing a user's Discord/subscription info.
 * Displays connection status, subscription info, and provides actions:
 * - Disconnect (with reason field)
 * - Trigger Sync
 * - Audit log section
 */
export function AdminUserDiscordPanel({ userId }: AdminUserDiscordPanelProps) {
  const [userInfo, setUserInfo] = useState<AdminDiscordUserInfo | null>(null);
  const [auditLog, setAuditLog] = useState<AuditEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuditLoading, setIsAuditLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Action states
  const [disconnectReason, setDisconnectReason] = useState('');
  const [isDisconnecting, setIsDisconnecting] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchUserInfo = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data, error: apiError } = await apiClient.get<AdminDiscordUserInfo>(
        `/admin/discord/users/${encodeURIComponent(userId)}`
      );
      if (apiError) {
        setError(apiError);
        return;
      }
      if (data) {
        setUserInfo(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch user Discord info');
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  const fetchAuditLog = useCallback(async () => {
    setIsAuditLoading(true);
    try {
      const { data } = await apiClient.get<{ audit_log: AuditEntry[] }>(
        `/admin/discord/users/${encodeURIComponent(userId)}/audit`
      );
      if (data?.audit_log) {
        setAuditLog(data.audit_log);
      }
    } catch {
      // Silently fail on audit log fetch
    } finally {
      setIsAuditLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchUserInfo();
    fetchAuditLog();
  }, [fetchUserInfo, fetchAuditLog]);

  const handleDisconnect = async () => {
    if (disconnectReason.length < 5 || disconnectReason.length > 500) {
      setActionMessage({ type: 'error', text: 'Reason must be between 5 and 500 characters.' });
      return;
    }

    setIsDisconnecting(true);
    setActionMessage(null);
    try {
      const { error: apiError } = await apiClient.delete<{ message: string }>(
        `/admin/discord/users/${encodeURIComponent(userId)}/disconnect`
      );
      if (apiError) {
        setActionMessage({ type: 'error', text: apiError });
      } else {
        setActionMessage({ type: 'success', text: 'Discord disconnected successfully.' });
        setDisconnectReason('');
        // Refresh data
        fetchUserInfo();
        fetchAuditLog();
      }
    } catch (err) {
      setActionMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Disconnect failed',
      });
    } finally {
      setIsDisconnecting(false);
    }
  };

  const handleTriggerSync = async () => {
    setIsSyncing(true);
    setActionMessage(null);
    try {
      const { error: apiError } = await apiClient.post<{ message: string }>(
        `/admin/discord/users/${encodeURIComponent(userId)}/sync`,
        {}
      );
      if (apiError) {
        setActionMessage({ type: 'error', text: apiError });
      } else {
        setActionMessage({ type: 'success', text: 'Sync triggered successfully.' });
        // Refresh after a short delay to allow sync to process
        setTimeout(() => {
          fetchUserInfo();
          fetchAuditLog();
        }, 2000);
      }
    } catch (err) {
      setActionMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Sync trigger failed',
      });
    } finally {
      setIsSyncing(false);
    }
  };

  const formatTimestamp = (ts: string | null | undefined) => {
    if (!ts) return 'N/A';
    try {
      return new Date(ts).toLocaleString();
    } catch {
      return ts;
    }
  };

  if (isLoading) {
    return (
      <Card padding="md">
        <div className="flex items-center justify-center py-8">
          <Spinner size="md" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card padding="md">
        <div className="text-center py-6">
          <p className="text-red-600 dark:text-red-400 mb-3 text-sm">{error}</p>
          <Button variant="ghost" size="sm" onClick={fetchUserInfo}>
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Discord & Subscription Info */}
      <Card padding="md">
        <div className="flex items-center space-x-2 mb-4">
          <DiscordIcon className="w-5 h-5 text-[#5865F2]" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Discord & Subscription
          </h3>
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <InfoRow label="Connection" value={userInfo?.connection_status || 'Not connected'} />
          <InfoRow label="Discord Username" value={userInfo?.discord_username || 'N/A'} />
          <InfoRow label="Discord User ID" value={userInfo?.discord_user_id || 'N/A'} />
          <InfoRow label="Verification" value={userInfo?.verification_status || 'N/A'} />
          <InfoRow label="Guild Membership" value={userInfo?.guild_membership_status || 'N/A'} />
          <InfoRow label="Membership Tier" value={userInfo?.membership_tier || 'FREE'} />
          <InfoRow label="Discord Role" value={userInfo?.current_discord_role || 'N/A'} />
          <InfoRow label="Stripe Status" value={userInfo?.stripe_subscription_status || 'N/A'} />
          <InfoRow
            label="Last Synced"
            value={formatTimestamp(userInfo?.last_synced_at)}
          />
        </div>
      </Card>

      {/* Actions */}
      <Card padding="md">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
          Actions
        </h3>

        {/* Action message */}
        {actionMessage && (
          <div
            className={`mb-3 px-3 py-2 rounded-lg text-sm ${
              actionMessage.type === 'success'
                ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
            }`}
          >
            {actionMessage.text}
          </div>
        )}

        {/* Trigger Sync */}
        <div className="mb-4">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleTriggerSync}
            disabled={isSyncing}
          >
            {isSyncing ? 'Syncing...' : 'Trigger Sync'}
          </Button>
        </div>

        {/* Disconnect */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
          <label
            htmlFor={`disconnect-reason-${userId}`}
            className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            Disconnect Reason (5-500 characters)
          </label>
          <textarea
            id={`disconnect-reason-${userId}`}
            value={disconnectReason}
            onChange={(e) => setDisconnectReason(e.target.value)}
            placeholder="Enter reason for disconnection..."
            className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-400 resize-none"
            rows={2}
            maxLength={500}
          />
          <div className="flex items-center justify-between mt-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {disconnectReason.length}/500
            </span>
            <Button
              variant="danger"
              size="sm"
              onClick={handleDisconnect}
              disabled={isDisconnecting || disconnectReason.length < 5}
            >
              {isDisconnecting ? 'Disconnecting...' : 'Disconnect'}
            </Button>
          </div>
        </div>
      </Card>

      {/* Audit Log */}
      <Card padding="md">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
          Audit Log
        </h3>

        {isAuditLoading ? (
          <div className="flex items-center justify-center py-4">
            <Spinner size="sm" />
          </div>
        ) : auditLog.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">No audit entries found.</p>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {auditLog.map((entry, index) => (
              <div
                key={index}
                className="flex items-start space-x-3 px-3 py-2 rounded-lg border border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800"
              >
                <div className="flex-shrink-0 mt-0.5">
                  <AuditEventIcon eventType={entry.event_type} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-gray-900 dark:text-gray-100">
                      {formatEventType(entry.event_type)}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap ml-2">
                      {formatTimestamp(entry.timestamp)}
                    </span>
                  </div>
                  {entry.actor && (
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      by {entry.actor}
                    </p>
                  )}
                  {entry.reason && (
                    <p className="text-xs text-gray-600 dark:text-gray-300 mt-0.5">
                      {entry.reason}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-xs text-gray-500 dark:text-gray-400">{label}</span>
      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{value}</p>
    </div>
  );
}

function AuditEventIcon({ eventType }: { eventType: string }) {
  const type = eventType.toLowerCase();

  if (type.includes('connected') || type.includes('joined') || type.includes('verified')) {
    return (
      <span className="inline-block w-2 h-2 rounded-full bg-green-500" aria-hidden="true" />
    );
  }
  if (type.includes('disconnected') || type.includes('removed') || type.includes('failed')) {
    return (
      <span className="inline-block w-2 h-2 rounded-full bg-red-500" aria-hidden="true" />
    );
  }
  if (type.includes('sync') || type.includes('reconciliation')) {
    return (
      <span className="inline-block w-2 h-2 rounded-full bg-blue-500" aria-hidden="true" />
    );
  }
  return (
    <span className="inline-block w-2 h-2 rounded-full bg-gray-400" aria-hidden="true" />
  );
}

function formatEventType(eventType: string): string {
  return eventType
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
