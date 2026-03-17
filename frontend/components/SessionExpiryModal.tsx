'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface SessionExpiryModalProps {
  remainingSeconds: number;
  onExtendSession: () => Promise<void>;
  onLogout: () => void;
}

function formatTime(seconds: number): string {
  const mins = Math.max(0, Math.floor(seconds / 60));
  const secs = Math.max(0, seconds % 60);
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

export function SessionExpiryModal({
  remainingSeconds,
  onExtendSession,
  onLogout,
}: SessionExpiryModalProps) {
  const [timeLeft, setTimeLeft] = useState(remainingSeconds);
  const [isExtending, setIsExtending] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Animate in on mount
  useEffect(() => {
    setTimeout(() => setIsVisible(true), 10);
  }, []);

  // Store the previously focused element and focus first button on mount
  useEffect(() => {
    previousFocusRef.current = document.activeElement as HTMLElement;

    // Focus the first focusable element in the modal
    const firstButton = modalRef.current?.querySelector<HTMLElement>('button');
    firstButton?.focus();

    return () => {
      previousFocusRef.current?.focus();
    };
  }, []);

  // Countdown timer
  useEffect(() => {
    setTimeLeft(remainingSeconds);
  }, [remainingSeconds]);

  useEffect(() => {
    if (timeLeft <= 0) {
      onLogout();
      return;
    }

    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        const next = prev - 1;
        if (next <= 0) {
          clearInterval(interval);
          return 0;
        }
        return next;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [timeLeft <= 0, onLogout]); // eslint-disable-line react-hooks/exhaustive-deps

  // Focus trapping
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onLogout();
        return;
      }

      if (e.key !== 'Tab') return;

      const modal = modalRef.current;
      if (!modal) return;

      const focusableElements = modal.querySelectorAll<HTMLElement>(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );

      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    },
    [onLogout]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Prevent body scroll while modal is open
  useEffect(() => {
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, []);

  const handleExtendSession = async () => {
    setIsExtending(true);
    try {
      await onExtendSession();
    } catch {
      setIsExtending(false);
    }
  };

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-opacity duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
      role="dialog"
      aria-modal="true"
      aria-labelledby="session-expiry-title"
      aria-describedby="session-expiry-description"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

      {/* Modal */}
      <div
        ref={modalRef}
        className={`relative w-full max-w-md transform transition-all duration-300 ${
          isVisible ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        }`}
      >
        <Card padding="lg">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="mb-4">
              <svg
                className="w-16 h-16 mx-auto text-amber-500 dark:text-amber-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h2
              id="session-expiry-title"
              className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2"
            >
              Session Expiring Soon
            </h2>
            <p
              id="session-expiry-description"
              className="text-gray-600 dark:text-gray-400"
            >
              Your session will expire in
            </p>
          </div>

          {/* Countdown */}
          <div className="text-center mb-6">
            <div
              className="text-5xl font-bold text-amber-500 dark:text-amber-400 tabular-nums p-6 rounded-lg bg-gray-50 dark:bg-gray-800/50"
              aria-live="polite"
              aria-atomic="true"
            >
              {formatTime(timeLeft)}
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-3">
            <Button
              variant="primary"
              onClick={handleExtendSession}
              disabled={isExtending}
            >
              {isExtending ? 'Extending...' : 'Extend Session'}
            </Button>
            <Button variant="ghost" onClick={onLogout}>
              Log Out
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
