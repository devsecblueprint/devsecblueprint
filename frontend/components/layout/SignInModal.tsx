'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { Spinner } from '@/components/ui/Spinner';

interface SignInModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SignInModal({ isOpen, onClose }: SignInModalProps) {
  const [loadingProvider, setLoadingProvider] = useState<'github' | 'gitlab' | null>(null);
  const modalRef = useRef<HTMLDivElement>(null);
  const firstButtonRef = useRef<HTMLButtonElement>(null);

  const handleSignIn = (provider: 'github' | 'gitlab') => {
    setLoadingProvider(provider);
    window.location.href =
      provider === 'github'
        ? apiClient.getAuthStartUrl()
        : apiClient.getGitLabAuthStartUrl();
  };

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
        return;
      }
      // Focus trap
      if (e.key === 'Tab' && modalRef.current) {
        const focusable = modalRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    },
    [onClose]
  );

  useEffect(() => {
    if (!isOpen) return;
    document.addEventListener('keydown', handleKeyDown);
    // Focus first button when modal opens
    setTimeout(() => firstButtonRef.current?.focus(), 0);
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  const isLoading = loadingProvider !== null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="sign-in-modal-title"
        className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl p-8 w-full max-w-sm mx-4"
      >
        <h2
          id="sign-in-modal-title"
          className="text-xl font-bold text-gray-900 dark:text-gray-100 text-center mb-6"
        >
          Sign in to DSB
        </h2>

        <div className="space-y-3">
          {/* GitHub button */}
          <button
            ref={firstButtonRef}
            onClick={() => handleSignIn('github')}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-lg text-white font-semibold transition-opacity focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ backgroundColor: '#24292e' }}
          >
            {loadingProvider === 'github' ? (
              <Spinner size="sm" />
            ) : (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 16 16" aria-hidden="true">
                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
              </svg>
            )}
            <span>{loadingProvider === 'github' ? 'Redirecting...' : 'Sign in with GitHub'}</span>
          </button>

          {/* GitLab button */}
          <button
            onClick={() => handleSignIn('gitlab')}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-lg text-white font-semibold transition-opacity focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-400 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ backgroundColor: '#FC6D26' }}
          >
            {loadingProvider === 'gitlab' ? (
              <Spinner size="sm" />
            ) : (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 512 512" aria-hidden="true">
                <path d="M503.5 204.6L502.8 202.8L433.1 21C431.7 17.5 429.2 14.4 425.9 12.4C422.8 10.4 419.3 9.4 415.8 9.4C412.2 9.4 408.7 10.5 405.7 12.6C402.6 14.7 400.3 17.7 399 21.2L347.2 168.2H164.8L113 21.2C111.7 17.7 109.4 14.7 106.3 12.6C103.3 10.5 99.8 9.4 96.2 9.4C92.7 9.4 89.2 10.4 86.1 12.4C82.8 14.4 80.3 17.5 78.9 21L9.2 202.8L8.5 204.6C-1.5 230.8-2.7 259.6 5 286.3C12.6 313 29.1 336.3 51.7 352.6L52.7 353.3L55.7 355.5L163.3 434.4L216.4 473.2L248.4 496.5C253.3 500.2 258.6 502 264 502C269.4 502 274.7 500.2 279.6 496.5L311.6 473.2L364.7 434.4L459.3 353.3L460.3 352.6C482.9 336.3 499.4 313 507 286.3C514.7 259.6 513.5 230.8 503.5 204.6Z" />
              </svg>
            )}
            <span>{loadingProvider === 'gitlab' ? 'Redirecting...' : 'Sign in with GitLab'}</span>
          </button>
        </div>

        <button
          onClick={onClose}
          disabled={isLoading}
          className="mt-6 w-full text-center text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
