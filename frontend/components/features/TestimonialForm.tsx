'use client';

import { useEffect, useState, useRef } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { apiClient } from '@/lib/api';
import type { TestimonialRecord } from '@/lib/types';
import {
  validateDisplayName,
  validateLinkedInUrl,
  validateQuote,
} from '@/lib/validation';

export interface TestimonialFormProps {
  isOpen: boolean;
  onClose: () => void;
}

interface FormState {
  displayName: string;
  anonymous: boolean;
  linkedinUrl: string;
  quote: string;
}

interface FieldErrors {
  displayName: string | null;
  linkedinUrl: string | null;
  quote: string | null;
}

type ViewState = 'loading' | 'empty' | 'editable' | 'readonly' | 'submitted';

const MAX_QUOTE_CHARS = 350;

function countChars(text: string): number {
  return text.length;
}

export function TestimonialForm({ isOpen, onClose }: TestimonialFormProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [viewState, setViewState] = useState<ViewState>('loading');
  const [formState, setFormState] = useState<FormState>({
    displayName: '',
    anonymous: false,
    linkedinUrl: '',
    quote: '',
  });
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({
    displayName: null,
    linkedinUrl: null,
    quote: null,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [existingTestimonial, setExistingTestimonial] = useState<TestimonialRecord | null>(null);

  const modalRef = useRef<HTMLDivElement>(null);
  const firstInputRef = useRef<HTMLInputElement>(null);
  const previousActiveElementRef = useRef<HTMLElement | null>(null);

  // Fetch existing testimonial on mount
  useEffect(() => {
    if (!isOpen) return;

    let cancelled = false;

    async function fetchExisting() {
      setViewState('loading');
      try {
        const { data, error, statusCode } = await apiClient.getMyTestimonial();

        if (cancelled) return;

        if (statusCode === 404 || error || !data) {
          // No existing testimonial
          setExistingTestimonial(null);
          setViewState('empty');
          setFormState({ displayName: '', anonymous: false, linkedinUrl: '', quote: '' });
          return;
        }

        // Backend wraps the record in { testimonial: {...} }
        const responseData = data as unknown as Record<string, unknown>;
        const record = (responseData.testimonial ?? responseData) as TestimonialRecord;
        setExistingTestimonial(record);

        if (record.status === 'approved') {
          setViewState('readonly');
        } else {
          // pending — editable pre-populated form
          const isAnon = record.display_name === 'Anonymous';
          setFormState({
            displayName: isAnon ? '' : record.display_name,
            anonymous: isAnon,
            linkedinUrl: record.linkedin_url || '',
            quote: record.quote,
          });
          setViewState('editable');
        }
      } catch {
        if (!cancelled) {
          setExistingTestimonial(null);
          setViewState('empty');
        }
      }
    }

    fetchExisting();
    return () => { cancelled = true; };
  }, [isOpen]);

  // Modal visibility animation and focus management
  useEffect(() => {
    if (isOpen) {
      window.dispatchEvent(new CustomEvent('modal:open'));
      previousActiveElementRef.current = document.activeElement as HTMLElement;
      setTimeout(() => setIsVisible(true), 10);
      setTimeout(() => firstInputRef.current?.focus(), 100);
    } else {
      setIsVisible(false);
      if (previousActiveElementRef.current) {
        previousActiveElementRef.current.focus();
      }
      window.dispatchEvent(new CustomEvent('modal:close'));
    }
  }, [isOpen]);

  // Escape key and focus trap
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    const handleTab = (e: KeyboardEvent) => {
      if (!isOpen || e.key !== 'Tab' || !modalRef.current) return;

      const focusableElements = modalRef.current.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const focusableArray = Array.from(focusableElements);
      const firstElement = focusableArray[0];
      const lastElement = focusableArray[focusableArray.length - 1];

      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement?.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement?.focus();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.addEventListener('keydown', handleTab);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.removeEventListener('keydown', handleTab);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  // Validate all fields, returns true if valid
  function validateForm(): boolean {
    const nameToValidate = formState.anonymous ? 'Anonymous' : formState.displayName;
    const errors: FieldErrors = {
      displayName: formState.anonymous ? null : validateDisplayName(nameToValidate),
      linkedinUrl: formState.anonymous ? null : validateLinkedInUrl(formState.linkedinUrl),
      quote: validateQuote(formState.quote),
    };
    setFieldErrors(errors);
    return !errors.displayName && !errors.linkedinUrl && !errors.quote;
  }

  // Handle field changes
  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    setFormState((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));

    // Clear field error on change
    if (name in fieldErrors) {
      setFieldErrors((prev) => ({ ...prev, [name]: null }));
    }
  }

  // Handle anonymous toggle
  function handleAnonymousToggle(e: React.ChangeEvent<HTMLInputElement>) {
    const checked = e.target.checked;
    setFormState((prev) => ({
      ...prev,
      anonymous: checked,
      ...(checked ? { displayName: '', linkedinUrl: '' } : {}),
    }));
    setFieldErrors((prev) => ({
      ...prev,
      displayName: null,
      linkedinUrl: null,
    }));
  }

  // Handle form submission
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!validateForm()) return;

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const payload: { display_name: string; linkedin_url?: string; quote: string } = {
        display_name: formState.anonymous ? 'Anonymous' : formState.displayName.trim(),
        quote: formState.quote.trim(),
      };

      if (!formState.anonymous && formState.linkedinUrl.trim()) {
        payload.linkedin_url = formState.linkedinUrl.trim();
      }

      const { error } = await apiClient.submitTestimonial(payload);

      if (error) {
        throw new Error(error);
      }

      setViewState('submitted');
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : 'Failed to submit testimonial. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  // Handle cancel / close
  function handleCancel() {
    onClose();
    setTimeout(() => {
      setFormState({ displayName: '', anonymous: false, linkedinUrl: '', quote: '' });
      setFieldErrors({ displayName: null, linkedinUrl: null, quote: null });
      setSubmitError(null);
      setViewState('loading');
    }, 300);
  }

  if (!isOpen) return null;

  const charCount = countChars(formState.quote);

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-opacity duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
      role="dialog"
      aria-modal="true"
      aria-labelledby="testimonial-modal-title"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

      {/* Modal */}
      <div
        ref={modalRef}
        className={`relative w-full max-w-2xl transform transition-all duration-300 max-h-[90vh] overflow-y-auto ${
          isVisible ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        <Card padding="lg">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2
              id="testimonial-modal-title"
              className="text-2xl font-bold text-gray-900 dark:text-gray-100"
            >
              {viewState === 'readonly'
                ? 'Your Testimonial'
                : viewState === 'submitted'
                ? 'Thank You!'
                : 'Share Your Testimonial'}
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

          {/* Loading State */}
          {viewState === 'loading' && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100" />
            </div>
          )}

          {/* Submitted Confirmation */}
          {viewState === 'submitted' && (
            <div className="space-y-6">
              <div className="p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
                <p className="text-green-800 dark:text-green-200 text-sm font-medium">
                  Your testimonial has been submitted for review. Thank you for sharing your experience!
                </p>
              </div>
              <div className="flex justify-end">
                <Button type="button" variant="secondary" onClick={handleCancel}>
                  Close
                </Button>
              </div>
            </div>
          )}

          {/* Read-only View (approved) */}
          {viewState === 'readonly' && existingTestimonial && (
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs font-semibold">
                <span className="w-2 h-2 rounded-full bg-green-500" />
                Approved
              </div>
              <div className="space-y-4">
                <div>
                  <span className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Display Name
                  </span>
                  <p className="text-gray-900 dark:text-gray-100">
                    {existingTestimonial.display_name}
                  </p>
                </div>
                {existingTestimonial.linkedin_url && (
                  <div>
                    <span className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      LinkedIn URL
                    </span>
                    <p className="text-gray-900 dark:text-gray-100">
                      {existingTestimonial.linkedin_url}
                    </p>
                  </div>
                )}
                <div>
                  <span className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Quote
                  </span>
                  <p className="text-gray-900 dark:text-gray-100 whitespace-pre-wrap">
                    {existingTestimonial.quote}
                  </p>
                </div>
                {existingTestimonial.admin_note && (
                  <div className="mt-4 p-4 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                    <span className="block text-xs font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400 mb-1">
                      Admin Note
                    </span>
                    <p className="text-sm text-blue-900 dark:text-blue-100 italic">
                      &ldquo;{existingTestimonial.admin_note}&rdquo;
                    </p>
                    {existingTestimonial.reviewed_by && (
                      <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
                        — {existingTestimonial.reviewed_by}
                      </p>
                    )}
                  </div>
                )}
              </div>
              <div className="flex justify-end">
                <Button type="button" variant="secondary" onClick={handleCancel}>
                  Close
                </Button>
              </div>
            </div>
          )}

          {/* Form (empty or editable) */}
          {(viewState === 'empty' || viewState === 'editable') && (
            <form onSubmit={handleSubmit} className="space-y-6" noValidate>
              {/* Pending status badge for existing testimonials */}
              {viewState === 'editable' && (
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 text-xs font-semibold">
                  <span className="w-2 h-2 rounded-full bg-amber-500" />
                  Pending Review
                </div>
              )}
              {/* Admin note from moderation */}
              {viewState === 'editable' && existingTestimonial?.admin_note && (
                <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                  <span className="block text-xs font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400 mb-1">
                    Admin Note
                  </span>
                  <p className="text-sm text-blue-900 dark:text-blue-100 italic">
                    &ldquo;{existingTestimonial.admin_note}&rdquo;
                  </p>
                  {existingTestimonial.reviewed_by && (
                    <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
                      — {existingTestimonial.reviewed_by}
                    </p>
                  )}
                </div>
              )}
              {/* Anonymous Toggle */}
              <div className="flex items-start">
                <div className="flex items-center h-5">
                  <input
                    type="checkbox"
                    id="anonymous"
                    name="anonymous"
                    checked={formState.anonymous}
                    onChange={handleAnonymousToggle}
                    className="w-4 h-4 rounded border-gray-300 dark:border-gray-700 text-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
                  />
                </div>
                <label
                  htmlFor="anonymous"
                  className="ml-3 text-sm text-gray-700 dark:text-gray-300"
                >
                  Submit anonymously
                </label>
              </div>

              {/* Display Name Field */}
              <div>
                <label
                  htmlFor="displayName"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  Display Name
                  {!formState.anonymous && (
                    <span className="text-red-500 ml-1" aria-hidden="true">*</span>
                  )}
                </label>
                <input
                  ref={firstInputRef}
                  type="text"
                  id="displayName"
                  name="displayName"
                  value={formState.anonymous ? 'Anonymous' : formState.displayName}
                  onChange={handleChange}
                  disabled={formState.anonymous}
                  className={`w-full px-4 py-3 rounded-lg border ${
                    fieldErrors.displayName
                      ? 'border-red-500 focus:ring-red-500'
                      : 'border-gray-300 dark:border-gray-700 focus:ring-blue-500'
                  } bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:border-transparent transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
                  placeholder="Enter your display name"
                  aria-required={!formState.anonymous}
                  aria-invalid={!!fieldErrors.displayName}
                  aria-describedby={fieldErrors.displayName ? 'displayName-error' : undefined}
                />
                {fieldErrors.displayName && (
                  <p id="displayName-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
                    {fieldErrors.displayName}
                  </p>
                )}
              </div>

              {/* LinkedIn URL Field */}
              <div>
                <label
                  htmlFor="linkedinUrl"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  LinkedIn URL
                  <span className="text-gray-500 dark:text-gray-400 text-xs ml-2">(optional)</span>
                </label>
                <input
                  type="url"
                  id="linkedinUrl"
                  name="linkedinUrl"
                  value={formState.anonymous ? '' : formState.linkedinUrl}
                  onChange={handleChange}
                  disabled={formState.anonymous}
                  className={`w-full px-4 py-3 rounded-lg border ${
                    fieldErrors.linkedinUrl
                      ? 'border-red-500 focus:ring-red-500'
                      : 'border-gray-300 dark:border-gray-700 focus:ring-blue-500'
                  } bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:border-transparent transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
                  placeholder="https://www.linkedin.com/in/your-profile"
                  aria-invalid={!!fieldErrors.linkedinUrl}
                  aria-describedby={fieldErrors.linkedinUrl ? 'linkedinUrl-error' : undefined}
                />
                {fieldErrors.linkedinUrl && (
                  <p id="linkedinUrl-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
                    {fieldErrors.linkedinUrl}
                  </p>
                )}
              </div>

              {/* Quote Field */}
              <div>
                <label
                  htmlFor="quote"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  Your Testimonial
                  <span className="text-red-500 ml-1" aria-hidden="true">*</span>
                </label>
                <textarea
                  id="quote"
                  name="quote"
                  value={formState.quote}
                  onChange={handleChange}
                  rows={4}
                  className={`w-full px-4 py-3 rounded-lg border ${
                    fieldErrors.quote
                      ? 'border-red-500 focus:ring-red-500'
                      : 'border-gray-300 dark:border-gray-700 focus:ring-blue-500'
                  } bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:border-transparent transition-colors resize-vertical`}
                  placeholder="Share your experience with the DSB platform..."
                  aria-required="true"
                  aria-invalid={!!fieldErrors.quote}
                  aria-describedby="quote-charcount quote-error"
                />
                <div className="flex items-center justify-between mt-1">
                  <p
                    id="quote-charcount"
                    className={`text-xs ${
                      charCount > MAX_QUOTE_CHARS
                        ? 'text-red-600 dark:text-red-400'
                        : 'text-gray-500 dark:text-gray-400'
                    }`}
                  >
                    {charCount}/{MAX_QUOTE_CHARS} characters
                  </p>
                </div>
                {fieldErrors.quote && (
                  <p id="quote-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
                    {fieldErrors.quote}
                  </p>
                )}
              </div>

              {/* Submit Error */}
              {submitError && (
                <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                  <p className="text-red-800 dark:text-red-200 text-sm font-medium" role="alert">
                    {submitError}
                  </p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-4 pt-4">
                <Button
                  type="submit"
                  variant="primary"
                  disabled={isSubmitting}
                  className="flex-1"
                >
                  {isSubmitting
                    ? 'Submitting...'
                    : viewState === 'editable'
                    ? 'Update Testimonial'
                    : 'Submit Testimonial'}
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={handleCancel}
                  disabled={isSubmitting}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </form>
          )}
        </Card>
      </div>
    </div>
  );
}
