'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import MarkdownRenderer from '@/components/MarkdownRenderer';
import type { BroadcastItem } from '@/lib/types';
import { format } from 'date-fns';

export function BroadcastManagement() {
  // Compose form state
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [link, setLink] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [composeError, setComposeError] = useState<string | null>(null);
  const [composeSuccess, setComposeSuccess] = useState<string | null>(null);

  // History state
  const [broadcasts, setBroadcasts] = useState<BroadcastItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    fetchBroadcasts();
  }, []);

  const fetchBroadcasts = async () => {
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
  };

  const handleSend = async () => {
    setComposeError(null);
    setComposeSuccess(null);

    if (!title.trim()) {
      setComposeError('Title is required');
      return;
    }
    if (title.trim().length > 100) {
      setComposeError('Title must be 100 characters or less');
      return;
    }
    if (!message.trim()) {
      setComposeError('Message is required');
      return;
    }
    if (message.trim().length > 2000) {
      setComposeError('Message must be 2000 characters or less');
      return;
    }

    setShowConfirm(true);
  };

  const confirmSend = async () => {
    setShowConfirm(false);
    setIsSending(true);
    setComposeError(null);

    try {
      const { data, error } = await apiClient.createBroadcast(
        title.trim(),
        message.trim(),
        link.trim() || undefined
      );
      if (error) {
        setComposeError(error);
        return;
      }
      setComposeSuccess('Broadcast sent to all users');
      setTitle('');
      setMessage('');
      setLink('');
      setShowPreview(false);
      setTimeout(() => setComposeSuccess(null), 5000);
      // Refresh history
      fetchBroadcasts();
    } catch (err) {
      setComposeError(err instanceof Error ? err.message : 'Failed to send broadcast');
    } finally {
      setIsSending(false);
    }
  };

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
      <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">
        Broadcast Notifications
      </h2>

      {/* Compose Form */}
      <div className="mb-8 rounded-lg border border-gray-200 dark:border-gray-700 p-5 space-y-4">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
          Send New Broadcast
        </h3>

        {/* Title */}
        <div>
          <label htmlFor="broadcast-title" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Title <span className="text-gray-400">({title.length}/100)</span>
          </label>
          <input
            id="broadcast-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength={100}
            placeholder="e.g. New Walkthrough Available!"
            className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
        </div>

        {/* Message with preview toggle */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label htmlFor="broadcast-message" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Message (Markdown) <span className="text-gray-400">({message.length}/2000)</span>
            </label>
            <button
              type="button"
              onClick={() => setShowPreview(!showPreview)}
              className="text-xs font-medium text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300"
            >
              {showPreview ? 'Edit' : 'Preview'}
            </button>
          </div>
          {showPreview ? (
            <div className="min-h-[120px] rounded-md border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 p-3 overflow-y-auto max-h-[200px]">
              {message.trim() ? (
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <MarkdownRenderer markdown={message} />
                </div>
              ) : (
                <p className="text-sm text-gray-400 italic">Nothing to preview</p>
              )}
            </div>
          ) : (
            <textarea
              id="broadcast-message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              maxLength={2000}
              rows={5}
              placeholder="Write your announcement in markdown..."
              className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-500 resize-y"
            />
          )}
        </div>

        {/* Link */}
        <div>
          <label htmlFor="broadcast-link" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Link (optional)
          </label>
          <input
            id="broadcast-link"
            type="text"
            value={link}
            onChange={(e) => setLink(e.target.value)}
            placeholder="/walkthroughs/new-walkthrough or https://..."
            className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-3">
          <Button
            variant="primary"
            size="sm"
            onClick={handleSend}
            disabled={isSending || !title.trim() || !message.trim()}
          >
            {isSending ? 'Sending...' : 'Send Broadcast'}
          </Button>
        </div>

        {/* Confirmation dialog */}
        {showConfirm && (
          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
            <p className="text-sm text-amber-800 dark:text-amber-200 mb-3">
              This will send an email to all registered users and show as a modal on their next login. Continue?
            </p>
            <div className="flex items-center space-x-2">
              <Button variant="primary" size="sm" onClick={confirmSend} disabled={isSending}>
                {isSending ? 'Sending...' : 'Confirm Send'}
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setShowConfirm(false)}>
                Cancel
              </Button>
            </div>
          </div>
        )}

        {composeSuccess && (
          <p className="text-sm text-green-600 dark:text-green-400">{composeSuccess}</p>
        )}
        {composeError && (
          <p className="text-sm text-red-600 dark:text-red-400">{composeError}</p>
        )}
      </div>

      {/* Broadcast History */}
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
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                    {broadcast.title}
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
    </div>
  );
}
