'use client';

import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import type { BroadcastItem } from '@/lib/types';
import { format } from 'date-fns';

/** `created_by` value written by the automatic announcement service. */
export const AUTO_ANNOUNCE_CREATOR = 'system:auto-announce';

interface BroadcastHistoryProps {
  /** Change this value to force the history to reload (e.g. after a send). */
  refreshKey?: number;
}

export function BroadcastHistory({ refreshKey = 0 }: BroadcastHistoryProps) {
  const [broadcasts, setBroadcasts] = useState<BroadcastItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchBroadcasts = useCallback(async () => {
    setIsLoading(true);
    setHistoryError(null);
    try {
      const { data, error } = await apiClient.getAdminBroadcasts();
      if (error) {
        setHistoryError(error);
        return;
      }
      if (data?.broadcasts) {
        setBroadcasts(data.broadcasts);
      }
    } catch (err) {
      setHistoryError(err instanceof Error ? err.message : 'Failed to load broadcasts');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBroadcasts();
  }, [fetchBroadcasts, refreshKey]);

  const handleDelete = async (broadcastId: string) => {
    if (!confirm('Delete this broadcast? This cannot be undone.')) return;
    setDeletingId(broadcastId);
    try {
      const { error } = await apiClient.deleteBroadcast(broadcastId);
      if (error) {
        setHistoryError(error);
        return;
      }
      setBroadcasts((prev) => prev.filter((b) => b.broadcast_id !== broadcastId));
    } catch (err) {
      setHistoryError(err instanceof Error ? err.message : 'Failed to delete');
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      return format(new Date(dateStr), 'MMM d, yyyy h:mm a');
    } catch {
      return dateStr;
    }
  };

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
        Broadcast History
      </h3>

      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <Spinner size="md" />
        </div>
      ) : historyError ? (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-sm text-red-800 dark:text-red-200">{historyError}</p>
          <button
            onClick={fetchBroadcasts}
            className="mt-2 text-sm font-medium text-red-600 dark:text-red-400 hover:text-red-700"
          >
            Try Again
          </button>
        </div>
      ) : broadcasts.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400 py-4">
          No broadcasts sent yet.
        </p>
      ) : (
        <div className="space-y-2">
          {broadcasts.map((broadcast) => (
            <div
              key={broadcast.broadcast_id}
              className="flex items-center justify-between rounded-lg border border-gray-200 dark:border-gray-700 px-4 py-3"
            >
              <div className="flex-1 min-w-0 mr-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                    {broadcast.title}
                  </span>
                  {broadcast.created_by === AUTO_ANNOUNCE_CREATOR && (
                    <span className="shrink-0 inline-flex px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                      Auto
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {formatDate(broadcast.created_at)} by {broadcast.created_by}
                </div>
              </div>
              <Button
                variant="danger"
                size="sm"
                onClick={() => handleDelete(broadcast.broadcast_id)}
                disabled={deletingId === broadcast.broadcast_id}
              >
                {deletingId === broadcast.broadcast_id ? 'Deleting...' : 'Delete'}
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
