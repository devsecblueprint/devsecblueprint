'use client';

import { useEffect, useState, useRef } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { apiClient } from '@/lib/api';

export interface SuccessStoryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface FormState {
  name: string;
  email: string;
  story: string;
  sharePublicly: boolean;
}

interface SubmissionState {
  isSubmitting: boolean;
  error: string | null;
  success: boolean;
}

export function SuccessStoryModal({ isOpen, onClose }: SuccessStoryModalProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [formState, setFormState] = useState<FormState>({
    name: '',
    email: '',
    story: '',
    sharePublicly: false
  });
  const [submissionState, setSubmissionState] = useState<SubmissionState>({
    isSubmitting: false,
    error: null,
    success: false
  });

  const modalRef = useRef<HTMLDivElement>(null);
  const firstInputRef = useRef<HTMLInputElement>(null);
  const previousActiveElementRef = useRef<HTMLElement | null>(null);

  // Handle modal visibility animation and focus management
  useEffect(() => {
    if (isOpen) {
      // Emit modal open event BEFORE any other actions
      window.dispatchEvent(new CustomEvent('modal:open'));
      
      // Store the currently focused element to restore later
      previousActiveElementRef.current = document.activeElement as HTMLElement;
      
      setTimeout(() => setIsVisible(true), 10);
      // Focus first input when modal opens
      setTimeout(() => firstInputRef.current?.focus(), 100);
    } else {
      setIsVisible(false);
      
      // Restore focus to the element that opened the modal
      if (previousActiveElementRef.current) {
        previousActiveElementRef.current.focus();
      }
      
      // Emit modal close event AFTER modal closes
      window.dispatchEvent(new CustomEvent('modal:close'));
    }
  }, [isOpen]);

  // Handle Escape key to close modal and focus trap
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    const handleTab = (e: KeyboardEvent) => {
      if (!isOpen || e.key !== 'Tab' || !modalRef.current) {
        return;
      }

      // Get all focusable elements within the modal
      const focusableElements = modalRef.current.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      
      const focusableArray = Array.from(focusableElements);
      const firstElement = focusableArray[0];
      const lastElement = focusableArray[focusableArray.length - 1];

      // If Shift+Tab on first element, focus last element
      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement?.focus();
      }
      // If Tab on last element, focus first element
      else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement?.focus();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.addEventListener('keydown', handleTab);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.removeEventListener('keydown', handleTab);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  // Email validation regex
  const isValidEmail = (email: string): boolean => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  // Form validation
  const isFormValid = (): boolean => {
    return (
      formState.name.trim() !== '' &&
      isValidEmail(formState.email) &&
      formState.story.trim() !== '' &&
      formState.story.trim().length >= 50
    );
  };

  // Handle form field changes
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    setFormState(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isFormValid()) {
      return;
    }

    setSubmissionState({
      isSubmitting: true,
      error: null,
      success: false
    });

    try {
      const { data, error } = await apiClient.sendSuccessStory(
        formState.name,
        formState.email,
        formState.story,
        formState.sharePublicly
      );

      if (error) {
        throw new Error(error);
      }

      // Success - display success message
      setSubmissionState({
        isSubmitting: false,
        error: null,
        success: true
      });

      // Auto-close modal after 2 seconds
      setTimeout(() => {
        onClose();
        // Reset form after modal closes
        setTimeout(() => {
          setFormState({
            name: '',
            email: '',
            story: '',
            sharePublicly: false
          });
          setSubmissionState({
            isSubmitting: false,
            error: null,
            success: false
          });
        }, 300);
      }, 2000);
    } catch (error) {
      // Error - display error message and keep modal open
      setSubmissionState({
        isSubmitting: false,
        error: 'Failed to send your story. Please try again later.',
        success: false
      });
    }
  };

  // Handle cancel
  const handleCancel = () => {
    onClose();
    // Reset form after modal closes
    setTimeout(() => {
      setFormState({
        name: '',
        email: '',
        story: '',
        sharePublicly: false
      });
      setSubmissionState({
        isSubmitting: false,
        error: null,
        success: false
      });
    }, 300);
  };

  // Handle click outside modal
  // Backdrop clicks should not close the modal to prevent accidental data loss
  // Users must use Cancel button, X button, or Escape key to close
  const handleBackdropClick = (e: React.MouseEvent) => {
    // Do nothing - backdrop clicks are disabled to preserve form data
  };

  if (!isOpen) return null;

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-opacity duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

      {/* Modal */}
      <div
        ref={modalRef}
        className={`relative w-full max-w-2xl transform transition-all duration-300 ${
          isVisible ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        <Card padding="lg">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2
              id="modal-title"
              className="text-2xl font-bold text-gray-900 dark:text-gray-100"
            >
              Share Your Success Story
            </h2>
            <button
              type="button"
              onClick={handleCancel}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-lg p-1"
              aria-label="Close modal"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Name Field */}
            <div>
              <label
                htmlFor="name"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                Name
              </label>
              <input
                ref={firstInputRef}
                type="text"
                id="name"
                name="name"
                value={formState.name}
                onChange={handleChange}
                className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                placeholder="Enter your name"
                required
              />
            </div>

            {/* Email Field */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                Email
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formState.email}
                onChange={handleChange}
                className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                placeholder="your.email@example.com"
                required
              />
            </div>

            {/* Story Field */}
            <div>
              <label
                htmlFor="story"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                Success Story
                <span className="text-gray-500 dark:text-gray-400 text-xs ml-2">
                  (minimum 50 characters)
                </span>
              </label>
              <textarea
                id="story"
                name="story"
                value={formState.story}
                onChange={handleChange}
                rows={6}
                className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors resize-vertical"
                placeholder="Share your experience and success with the community..."
                required
                minLength={50}
              />
              <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {formState.story.length} / 50 characters minimum
              </div>
            </div>

            {/* Share Publicly Checkbox */}
            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input
                  type="checkbox"
                  id="sharePublicly"
                  name="sharePublicly"
                  checked={formState.sharePublicly}
                  onChange={handleChange}
                  className="w-4 h-4 rounded border-gray-300 dark:border-gray-700 text-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
                />
              </div>
              <label
                htmlFor="sharePublicly"
                className="ml-3 text-sm text-gray-700 dark:text-gray-300"
              >
                I give permission to share my story publicly
              </label>
            </div>

            {/* Success Message */}
            {submissionState.success && (
              <div className="p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
                <p className="text-green-800 dark:text-green-200 text-sm font-medium">
                  Thank you for sharing your story!
                </p>
              </div>
            )}

            {/* Error Message */}
            {submissionState.error && (
              <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                <p className="text-red-800 dark:text-red-200 text-sm font-medium">
                  {submissionState.error}
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-4 pt-4">
              <Button
                type="submit"
                variant="primary"
                disabled={!isFormValid() || submissionState.isSubmitting}
                className="flex-1"
              >
                {submissionState.isSubmitting ? 'Sending...' : 'Send Story'}
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={handleCancel}
                disabled={submissionState.isSubmitting}
                className="flex-1"
              >
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
}
