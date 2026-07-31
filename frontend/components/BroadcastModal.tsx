'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { Card } from '@/components/ui/Card';
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
 * - Title and date (always visible)
 * - "Read More" toggle to expand full markdown body
 * - "Show Less" to collapse back
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
  const [isExpanded, setIsExpanded] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Animate in
  useEffect(() => {
    setTimeout(() => setIsVisible(true), 10);
  }, []);

  // Focus management
  useEffect(() => {
    previousFocusRef.current = document.activeElement as HTMLElement;
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

  // Collapse content when navigating between broadcasts
  useEffect(() => {
    setIsExpanded(false);
  }, [currentIndex]);

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

  /**
   * Generate a short preview from the markdown message.
   * Takes the first paragraph or first ~150 chars.
   */
  const getPreview = (message: string): string => {
    const firstParagraph = message.split('\n\n')[0] || message;
    if (firstParagraph.length <= 150) return firstParagraph;
    return firstParagraph.slice(0, 150).replace(/\s+\S*$/, '') + '…';
  };

  if (!current) return null;

  const hasLongContent = current.message.length > 150;

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-opacity duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
      onClick={handleDismissCurrent}
      role="dialog"
      aria-modal="true"
      aria-labelledby="broadcast-modal-title"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

      {/* Modal */}
      <div
        ref={modalRef}
        className={`relative w-full max-w-2xl max-h-[90vh] overflow-y-auto transform transition-all duration-300 ${
          isVisible ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        <Card padding="lg" className="m-2 sm:m-0">
          {/* Header */}
          <div className="text-center mb-4 sm:mb-6">
            <div className="mb-3 sm:mb-4">
              <svg
                className="w-12 h-12 sm:w-16 sm:h-16 mx-auto text-amber-500 dark:text-amber-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"
                />
              </svg>
            </div>
            <h2
              id="broadcast-modal-title"
              className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2"
            >
              {current.title}
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {formatDate(current.created_at)}
              {total > 1 && (
                <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                  {currentIndex + 1} of {total}
                </span>
              )}
            </p>
          </div>

          {/* Body — collapsed or expanded */}
          <div className="mb-6 sm:mb-8">
            {!isExpanded && hasLongContent ? (
              /* Collapsed: show preview + Read More */
              <div>
                <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mb-3">
                  {getPreview(current.message)}
                </p>
                <button
                  type="button"
                  onClick={() => setIsExpanded(true)}
                  className="inline-flex items-center gap-1 text-sm font-medium text-primary-500 dark:text-primary-400 hover:text-primary-600 dark:hover:text-primary-300 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 rounded"
                >
                  Read More
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              </div>
            ) : (
              /* Expanded: show full content */
              <div>
                <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 sm:p-6 overflow-hidden">
                  <div className="prose prose-sm dark:prose-invert max-w-none break-words prose-p:break-words prose-headings:break-words">
                    <MarkdownRenderer markdown={current.message} />
                  </div>
                </div>
                {hasLongContent && (
                  <button
                    type="button"
                    onClick={() => setIsExpanded(false)}
                    className="inline-flex items-center gap-1 mt-3 text-sm font-medium text-primary-500 dark:text-primary-400 hover:text-primary-600 dark:hover:text-primary-300 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 rounded"
                  >
                    Show Less
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                    </svg>
                  </button>
                )}
              </div>
            )}

            {/* Short messages render directly without toggle */}
            {!hasLongContent && !isExpanded && (
              <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 sm:p-6 overflow-hidden">
                <div className="prose prose-sm dark:prose-invert max-w-none break-words">
                  <MarkdownRenderer markdown={current.message} />
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-2 sm:gap-3">
            {/* CTA Link (if provided) */}
            {current.link && (
              <a
                href={current.link}
                className="inline-flex items-center justify-center px-4 sm:px-6 py-2.5 sm:py-3 text-sm sm:text-base bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
                target={current.link.startsWith('http') ? '_blank' : undefined}
                rel={current.link.startsWith('http') ? 'noopener noreferrer' : undefined}
                onClick={handleDismissCurrent}
              >
                <span>Check It Out</span>
                <svg className="w-4 h-4 sm:w-5 sm:h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </a>
            )}

            {/* Dismiss / Navigation row */}
            <div className="flex items-center justify-between">
              {/* Left: navigation */}
              <div className="flex items-center gap-2">
                {total > 1 && currentIndex > 0 && (
                  <button
                    onClick={handlePrev}
                    disabled={isDismissing}
                    className="inline-flex items-center px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors disabled:opacity-50"
                  >
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    Previous
                  </button>
                )}
                {total > 1 && currentIndex < total - 1 && (
                  <button
                    onClick={handleNext}
                    disabled={isDismissing}
                    className="inline-flex items-center px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors disabled:opacity-50"
                  >
                    Next
                    <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Right: dismiss actions */}
              <div className="flex items-center gap-2">
                {total > 1 && (
                  <button
                    onClick={handleDismissAll}
                    disabled={isDismissing}
                    className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors disabled:opacity-50"
                  >
                    Dismiss All
                  </button>
                )}
                <button
                  onClick={handleDismissCurrent}
                  disabled={isDismissing}
                  className="inline-flex items-center justify-center px-4 sm:px-6 py-2.5 sm:py-3 text-sm sm:text-base bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 font-semibold rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
                >
                  {isDismissing ? 'Dismissing...' : 'Got It'}
                </button>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
