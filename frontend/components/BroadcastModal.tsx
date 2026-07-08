'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import MarkdownRenderer from '@/components/MarkdownRenderer';
import type { BroadcastItem } from '@/lib/types';
import { format } from 'date-fns';

interface BroadcastModalProps {
  broadcasts: BroadcastItem[];
  onAllDismissed: () => void;
}

/**
 * BroadcastModal — stacked modal showing unread broadcast notifications.
 *
 * Displays broadcasts one at a time (oldest first) with:
 * - Title and date
 * - Markdown body rendered as HTML
 * - Optional CTA link button
 * - Dismiss / Dismiss All / Next navigation
 *
 * Accessible: focus trap, escape to close, aria-modal.
 */
export function BroadcastModal({ broadcasts: initialBroadcasts, onAllDismissed }: BroadcastModalProps) {
  const [broadcasts, setBroadcasts] = useState<BroadcastItem[]>(initialBroadcasts);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [isDismissing, setIsDismissing] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Animate in
  useEffect(() => {
    setTimeout(() => setIsVisible(true), 10);
  }, []);

  // Focus management
  useEffect(() => {
    previousFocusRef.current = document.activeElement as HTMLElement;
    const firstButton = modalRef.current?.querySelector<HTMLElement>('button');
    firstButton?.focus();
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
      if (e.key === 'Escape') {
        handleDismissCurrent();
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [currentIndex, broadcasts]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const current = broadcasts[currentIndex];
  const total = broadcasts.length;

  const handleDismissCurrent = async () => {
    if (!current || isDismissing) return;
    setIsDismissing(true);

    try {
      await apiClient.dismissBroadcast(current.broadcast_id);
    } catch (err) {
      console.error('Failed to dismiss broadcast:', err);
    }

    const remaining = broadcasts.filter((_, i) => i !== currentIndex);
    if (remaining.length === 0) {
      onAllDismissed();
    } else {
      setBroadcasts(remaining);
      setCurrentIndex(Math.min(currentIndex, remaining.length - 1));
    }
    setIsDismissing(false);
  };

  const handleDismissAll = async () => {
    if (isDismissing) return;
    setIsDismissing(true);

    try {
      await apiClient.dismissAllBroadcasts();
    } catch (err) {
      console.error('Failed to dismiss all broadcasts:', err);
    }

    onAllDismissed();
  };

  const handleNext = () => {
    if (currentIndex < total - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      return format(new Date(dateStr), 'MMM d, yyyy');
    } catch {
      return '';
    }
  };

  if (!current) return null;

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-opacity duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
      role="dialog"
      aria-modal="true"
      aria-labelledby="broadcast-modal-title"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Modal */}
      <div
        ref={modalRef}
        className={`relative w-full max-w-lg max-h-[80vh] flex flex-col transform transition-all duration-300 ${
          isVisible ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        }`}
      >
        <Card padding="lg">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <span className="text-xl" aria-hidden="true">📢</span>
              <span className="text-sm text-gray-500 dark:text-gray-400 font-medium">
                {currentIndex + 1} of {total}
              </span>
            </div>
            <button
              onClick={handleDismissCurrent}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              aria-label="Dismiss this announcement"
              disabled={isDismissing}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Title */}
          <h2
            id="broadcast-modal-title"
            className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-1"
          >
            {current.title}
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
            {formatDate(current.created_at)}
          </p>

          {/* Body — scrollable */}
          <div className="overflow-y-auto max-h-[40vh] mb-4 pr-1">
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <MarkdownRenderer markdown={current.message} />
            </div>
          </div>

          {/* CTA Link */}
          {current.link && (
            <div className="mb-4">
              <a
                href={current.link}
                className="inline-flex items-center px-4 py-2 bg-amber-500 hover:bg-amber-600 text-gray-900 font-semibold text-sm rounded-lg transition-colors"
                target={current.link.startsWith('http') ? '_blank' : undefined}
                rel={current.link.startsWith('http') ? 'noopener noreferrer' : undefined}
              >
                Learn More
                <svg className="w-4 h-4 ml-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </a>
            </div>
          )}

          {/* Footer actions */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-2">
              {total > 1 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handlePrev}
                  disabled={currentIndex === 0 || isDismissing}
                >
                  Previous
                </Button>
              )}
              {currentIndex < total - 1 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleNext}
                  disabled={isDismissing}
                >
                  Next
                </Button>
              )}
            </div>
            <div className="flex items-center space-x-2">
              {total > 1 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleDismissAll}
                  disabled={isDismissing}
                >
                  Dismiss All
                </Button>
              )}
              <Button
                variant="primary"
                size="sm"
                onClick={handleDismissCurrent}
                disabled={isDismissing}
              >
                {isDismissing ? 'Dismissing...' : 'Got It'}
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
