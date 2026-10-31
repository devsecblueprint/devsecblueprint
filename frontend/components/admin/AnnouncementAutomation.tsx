'use client';

import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import type { Announcement, AnnouncementStatus } from '@/lib/types';
import { format } from 'date-fns';

const STATUS_COLORS: Record<AnnouncementStatus, string> = {
  PENDING: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
  SENDING: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  SENT: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  FAILED: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  BASELINED: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
};

function formatDate(dateStr?: string | null) {
  if (!dateStr) return '—';
  try {
    return format(new Date(dateStr), 'MMM d, yyyy h:mm a');
  } catch {
    return dateStr;
  }
}

export function AnnouncementAutomation() {
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [retryingKey, setRetryingKey] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const [showBaselineConfirm, setShowBaselineConfirm] = useState(false);
  const [isBaselining, setIsBaselining] = useState(false);

  const fetchAnnouncements = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const { data, error } = await apiClient.getAnnouncements();
      if (error) {
        setLoadError(error);
        return;
      }
      if (data) {
        setEnabled(data.enabled);
        setAnnouncements(data.announcements ?? []);
      }
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Failed to load announcements');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnnouncements();
  }, [fetchAnnouncements]);

  // Close the confirmation dialog with Escape
  useEffect(() => {
    if (!showBaselineConfirm) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isBaselining) setShowBaselineConfirm(false);
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [showBaselineConfirm, isBaselining]);

  const handleRetry = async (contentKey: string) => {
    setActionError(null);
    setActionSuccess(null);
    setRetryingKey(contentKey);
    try {
      const { data, error } = await apiClient.retryAnnouncement(contentKey);
      if (error) {
        setActionError(error);
        return;
      }
      setActionSuccess(data?.message ?? 'Retry requested');
      await fetchAnnouncements();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to retry announcement');
    } finally {
      setRetryingKey(null);
    }
  };

  const handleConfirmBaseline = async () => {
    setActionError(null);
    setActionSuccess(null);
    setIsBaselining(true);
    try {
      const { data, error } = await apiClient.baselineAnnouncements();
      if (error) {
        setActionError(error);
        return;
      }
      setActionSuccess(
        data?.message ?? `Baselined ${data?.baselined ?? 0} walkthroughs`
      );
      await fetchAnnouncements();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to baseline walkthroughs');
    } finally {
      setIsBaselining(false);
      setShowBaselineConfirm(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header: status pill and baseline action */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
            Automatic Announcements
          </h3>
          {enabled !== null && (
            <span
              className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${
                enabled
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                  : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
              }`}
            >
              {enabled ? 'Enabled' : 'Disabled'}
            </span>
          )}
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setShowBaselineConfirm(true)}
          disabled={isBaselining}
        >
          Baseline walkthroughs
        </Button>
      </div>

      {enabled === false && (
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Automatic announcements are turned off. This flag is set via deployment configuration
          (<code className="text-xs">ANNOUNCEMENTS_ENABLED</code>) and cannot be changed here.
        </p>
      )}

      {actionSuccess && (
        <p role="status" className="text-sm text-green-600 dark:text-green-400">{actionSuccess}</p>
      )}
      {actionError && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">{actionError}</p>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <Spinner size="md" />
        </div>
      ) : loadError ? (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-sm text-red-800 dark:text-red-200">{loadError}</p>
          <button
            onClick={fetchAnnouncements}
            className="mt-2 text-sm font-medium text-red-600 dark:text-red-400 hover:text-red-700"
          >
            Try Again
          </button>
        </div>
      ) : announcements.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400 py-4">No announcements yet</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th scope="col" className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Type</th>
                <th scope="col" className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Title</th>
                <th scope="col" className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Status</th>
                <th scope="col" className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">First seen</th>
                <th scope="col" className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Sent at</th>
                <th scope="col" className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Attempts</th>
                <th scope="col" className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Last error</th>
                <th scope="col" className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Actions</th>
              </tr>
            </thead>
            <tbody>
              {announcements.map((a) => (
                <tr
                  key={a.content_key}
                  className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900/50"
                >
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-400 capitalize">{a.content_type}</td>
                  <td className="py-3 px-4 font-medium text-gray-900 dark:text-gray-100">{a.title}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${STATUS_COLORS[a.status] ?? STATUS_COLORS.PENDING}`}
                    >
                      {a.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{formatDate(a.first_seen_at)}</td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{formatDate(a.sent_at)}</td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{a.attempts}</td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-400 max-w-xs break-words">
                    {a.last_error || '—'}
                  </td>
                  <td className="py-3 px-4 text-right">
                    {a.status === 'FAILED' && (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleRetry(a.content_key)}
                        disabled={retryingKey !== null}
                        aria-label={`Retry ${a.title}`}
                      >
                        {retryingKey === a.content_key ? 'Retrying...' : 'Retry'}
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Baseline confirmation dialog */}
      {showBaselineConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => !isBaselining && setShowBaselineConfirm(false)}
            aria-hidden="true"
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="baseline-dialog-title"
            aria-describedby="baseline-dialog-desc"
            className="relative bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-md w-full mx-4 p-6"
          >
            <h2 id="baseline-dialog-title" className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-3">
              Baseline all walkthroughs?
            </h2>
            <p id="baseline-dialog-desc" className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              All current walkthroughs will be marked as already announced. No emails will be sent for
              them. Only walkthroughs added after this will trigger an announcement.
            </p>
            <div className="flex justify-end gap-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowBaselineConfirm(false)}
                disabled={isBaselining}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleConfirmBaseline}
                disabled={isBaselining}
              >
                {isBaselining ? 'Baselining...' : 'Confirm baseline'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
