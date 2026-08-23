'use client';

import { useState } from 'react';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface RevokeCredentialModalProps {
  isOpen: boolean;
  onClose: () => void;
  credentialId: string;
  holderName: string;
  pathwayName: string;
  onRevoked: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function RevokeCredentialModal({
  isOpen,
  onClose,
  credentialId,
  holderName,
  pathwayName,
  onRevoked,
}: RevokeCredentialModalProps) {
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reasonTrimmed = reason.trim();
  const isReasonValid =
    reasonTrimmed.length >= 5 && reasonTrimmed.length <= 500;

  const handleClose = () => {
    if (isSubmitting) return;
    setReason('');
    setError(null);
    onClose();
  };

  const handleRevoke = async () => {
    if (!isReasonValid || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const { error: apiError } = await apiClient.post(
        `/admin/certifications/credentials/${encodeURIComponent(credentialId)}/revoke`,
        { reason: reasonTrimmed }
      );

      if (apiError) {
        setError(apiError);
        return;
      }

      // Success
      setReason('');
      setError(null);
      onRevoked();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to revoke credential'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="revoke-modal-title"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 transition-opacity"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Modal content */}
      <div className="relative w-full max-w-md mx-4 bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700">
        {/* Header */}
        <div className="p-6 pb-0">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
              <svg
                className="w-5 h-5 text-red-600 dark:text-red-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>
            <div className="flex-1">
              <h2
                id="revoke-modal-title"
                className="text-lg font-semibold text-gray-900 dark:text-gray-100"
              >
                Revoke Credential
              </h2>
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                This action is irreversible. The credential holder will be
                notified.
              </p>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          {/* Credential summary */}
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 space-y-1">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500 dark:text-gray-400">
                Credential ID
              </span>
              <span className="font-mono text-gray-900 dark:text-gray-100">
                {credentialId}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500 dark:text-gray-400">Holder</span>
              <span className="text-gray-900 dark:text-gray-100">
                {holderName}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500 dark:text-gray-400">Pathway</span>
              <span className="text-gray-900 dark:text-gray-100">
                {pathwayName}
              </span>
            </div>
          </div>

          {/* Reason textarea */}
          <div>
            <label
              htmlFor="revoke-reason"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Revocation Reason <span className="text-red-500">*</span>
            </label>
            <textarea
              id="revoke-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Provide the reason for revoking this credential..."
              rows={3}
              maxLength={500}
              disabled={isSubmitting}
              className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-red-500 dark:focus:ring-red-400 resize-y disabled:opacity-50"
            />
            <div className="flex justify-between mt-1">
              <span className="text-xs text-gray-500 dark:text-gray-500">
                {reasonTrimmed.length < 5 && reasonTrimmed.length > 0
                  ? 'Minimum 5 characters required'
                  : '\u00A0'}
              </span>
              <span
                className={`text-xs ${
                  reasonTrimmed.length > 500
                    ? 'text-red-500'
                    : 'text-gray-500 dark:text-gray-500'
                }`}
              >
                {reasonTrimmed.length}/500
              </span>
            </div>
          </div>

          {/* Error */}
          {error && (
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 pb-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={handleRevoke}
            disabled={!isReasonValid || isSubmitting}
            aria-label="Confirm credential revocation"
          >
            {isSubmitting ? (
              <span className="flex items-center gap-2">
                <Spinner size="sm" />
                Revoking...
              </span>
            ) : (
              'Revoke Credential'
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
