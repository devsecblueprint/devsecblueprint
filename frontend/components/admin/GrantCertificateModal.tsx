'use client';

import { useEffect, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/Button';

interface GrantCertificateModalProps {
  /** Username of the learner receiving the certificate */
  username: string;
  /** Capstone/pathway display name */
  capstoneName: string;
  /** Whether the grant is in progress */
  isGranting?: boolean;
  /** Called when the admin confirms the grant */
  onConfirm: () => void;
  /** Called when the modal is closed/cancelled */
  onClose: () => void;
}

/**
 * GrantCertificateModal — Styled confirmation dialog for granting a certificate.
 *
 * Replaces the native window.confirm with a visually consistent modal that
 * matches the admin UI design system.
 */
export function GrantCertificateModal({
  username,
  capstoneName,
  isGranting = false,
  onConfirm,
  onClose,
}: GrantCertificateModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const confirmBtnRef = useRef<HTMLButtonElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Store previous focus and focus the confirm button
  useEffect(() => {
    previousFocusRef.current = document.activeElement as HTMLElement;
    confirmBtnRef.current?.focus();
    return () => {
      previousFocusRef.current?.focus();
    };
  }, []);

  // Prevent body scroll
  useEffect(() => {
    const original = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = original;
    };
  }, []);

  // Keyboard handling
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isGranting) {
        onClose();
      }
    },
    [onClose, isGranting]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="grant-cert-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={!isGranting ? onClose : undefined}
      />

      {/* Modal */}
      <div
        ref={modalRef}
        className="relative w-full max-w-md bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-200 dark:border-gray-800 overflow-hidden"
      >
        {/* Header */}
        <div className="px-6 pt-6 pb-4">
          <div className="flex items-center space-x-3 mb-4">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
              <svg
                className="w-5 h-5 text-green-600 dark:text-green-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"
                />
              </svg>
            </div>
            <h2
              id="grant-cert-title"
              className="text-lg font-semibold text-gray-900 dark:text-gray-100"
            >
              Grant Certificate
            </h2>
          </div>

          <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
            You are about to grant a certificate to{' '}
            <span className="font-semibold text-gray-900 dark:text-gray-100">{username}</span>{' '}
            for completing the{' '}
            <span className="font-semibold text-amber-600 dark:text-amber-400">{capstoneName}</span>.
          </p>

          <div className="mt-4 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
            <p className="text-xs text-amber-800 dark:text-amber-300 leading-relaxed">
              This will issue an official certificate, send a congratulations email to the learner, and cannot be easily undone.
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-800">
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            disabled={isGranting}
          >
            Cancel
          </Button>
          <button
            ref={confirmBtnRef}
            onClick={onConfirm}
            disabled={isGranting}
            className="inline-flex items-center px-4 py-2 text-sm font-semibold rounded-lg text-white bg-green-600 hover:bg-green-700 dark:bg-green-600 dark:hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
          >
            {isGranting ? (
              <>
                <svg className="animate-spin -ml-0.5 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Granting...
              </>
            ) : (
              'Grant Certificate'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
