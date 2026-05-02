'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/Button';
import MarkdownRenderer from '@/components/MarkdownRenderer';

interface FeedbackModalProps {
  /** Username of the learner being reviewed */
  username: string;
  /** Content ID of the capstone being reviewed */
  contentId: string;
  /** Whether the modal is submitting */
  isSubmitting?: boolean;
  /** Called when the admin submits feedback */
  onSubmit: (feedback: string) => void;
  /** Called when the modal is closed/cancelled */
  onClose: () => void;
}

/**
 * FeedbackModal — Modal dialog for admin capstone review.
 *
 * Provides a markdown text area with live preview toggle, submit/cancel buttons,
 * and empty-feedback validation. Fully accessible with focus trap, Escape to close,
 * and proper ARIA attributes.
 */
export function FeedbackModal({
  username,
  contentId,
  isSubmitting = false,
  onSubmit,
  onClose,
}: FeedbackModalProps) {
  const [feedback, setFeedback] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Animate in
  useEffect(() => {
    setTimeout(() => setIsVisible(true), 10);
  }, []);

  // Focus management — focus textarea on open, restore focus on close
  useEffect(() => {
    previousFocusRef.current = document.activeElement as HTMLElement;
    textareaRef.current?.focus();
    return () => {
      previousFocusRef.current?.focus();
    };
  }, []);

  // Prevent body scroll while modal is open
  useEffect(() => {
    const original = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = original;
    };
  }, []);

  // Keyboard handling: Escape to close + focus trap
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
        return;
      }
      if (e.key !== 'Tab') return;
      const modal = modalRef.current;
      if (!modal) return;
      const focusable = modal.querySelectorAll<HTMLElement>(
        'button:not([disabled]), textarea:not([disabled]), [href], [tabindex]:not([tabindex="-1"])'
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
    },
    [onClose]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const handleSubmit = () => {
    const trimmed = feedback.trim();
    if (!trimmed) {
      setValidationError('Feedback is required. Please provide review comments before submitting.');
      return;
    }
    setValidationError(null);
    onSubmit(trimmed);
  };

  const handleFeedbackChange = (value: string) => {
    setFeedback(value);
    if (validationError && value.trim()) {
      setValidationError(null);
    }
  };

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-opacity duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
      role="dialog"
      aria-modal="true"
      aria-labelledby="feedback-modal-title"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div
        ref={modalRef}
        className={`relative w-full max-w-3xl max-h-[85vh] flex flex-col bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 transform transition-all duration-300 ${
          isVisible ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2
              id="feedback-modal-title"
              className="text-lg font-semibold text-gray-900 dark:text-gray-100"
            >
              Review Capstone Submission
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
              {username} — {contentId}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            aria-label="Close modal"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {/* Toggle between Write and Preview */}
          <div className="flex items-center space-x-1 mb-3">
            <button
              type="button"
              onClick={() => setShowPreview(false)}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                !showPreview
                  ? 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
              }`}
            >
              Write
            </button>
            <button
              type="button"
              onClick={() => setShowPreview(true)}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                showPreview
                  ? 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
              }`}
            >
              Preview
            </button>
          </div>

          {/* Write mode */}
          {!showPreview && (
            <div>
              <textarea
                ref={textareaRef}
                value={feedback}
                onChange={(e) => handleFeedbackChange(e.target.value)}
                placeholder="Write your feedback in markdown..."
                className={`w-full h-64 px-4 py-3 rounded-lg border text-sm font-mono resize-y bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-400 ${
                  validationError
                    ? 'border-red-500 dark:border-red-500'
                    : 'border-gray-300 dark:border-gray-600'
                }`}
                aria-label="Feedback markdown editor"
                aria-invalid={!!validationError}
                aria-describedby={validationError ? 'feedback-error' : undefined}
                disabled={isSubmitting}
              />
              {validationError && (
                <p
                  id="feedback-error"
                  className="mt-2 text-sm text-red-600 dark:text-red-400"
                  role="alert"
                >
                  {validationError}
                </p>
              )}
            </div>
          )}

          {/* Preview mode */}
          {showPreview && (
            <div className="min-h-[16rem] rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-3 bg-white dark:bg-gray-800 overflow-y-auto">
              {feedback.trim() ? (
                <MarkdownRenderer markdown={feedback} />
              ) : (
                <p className="text-sm text-gray-400 dark:text-gray-500 italic">
                  Nothing to preview yet. Switch to Write mode to add feedback.
                </p>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
          <Button variant="ghost" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? 'Submitting...' : 'Submit Review'}
          </Button>
        </div>
      </div>
    </div>
  );
}
