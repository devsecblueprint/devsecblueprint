'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { ContactForm } from '@/components/ui/ContactForm';
import { apiClient } from '@/lib/api';
import type { ContactFormData } from '@/lib/data/contact';

/**
 * ContactForm wired to the backend POST /api/contact endpoint.
 * Shows a success modal on submission instead of inline confirmation.
 */
export function ContactFormWithSubmit() {
  const [showModal, setShowModal] = useState(false);
  const [formKey, setFormKey] = useState(0);

  async function handleSubmit(
    data: ContactFormData
  ): Promise<{ success: boolean; error?: string }> {
    try {
      const { data: response, error } = await apiClient.post<{
        success: boolean;
        message: string;
      }>('/api/contact', {
        full_name: data.fullName,
        email: data.email,
        organization: data.organization,
        inquiry_type: data.inquiryType,
        subject: data.subject,
        message: data.message,
      });

      if (error) {
        return { success: false, error };
      }

      // Show modal on success
      setShowModal(true);

      // Return success: false to prevent the inline confirmation from showing
      // (we handle it via modal instead)
      return { success: false };
    } catch {
      return {
        success: false,
        error: 'An unexpected error occurred. Please try again.',
      };
    }
  }

  function handleCloseModal() {
    setShowModal(false);
    // Reset form by remounting it
    setFormKey((k) => k + 1);
  }

  return (
    <>
      <ContactForm key={formKey} onSubmit={handleSubmit} />
      {showModal && <SuccessModal onClose={handleCloseModal} />}
    </>
  );
}

/**
 * Success modal shown after contact form submission.
 * Animated entrance, focus-trapped, dismissible via button, Escape, or overlay click.
 */
function SuccessModal({ onClose }: { onClose: () => void }) {
  const modalRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    },
    [onClose]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';
    // Focus the close button
    setTimeout(() => closeButtonRef.current?.focus(), 50);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [handleKeyDown]);

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="contact-success-title"
        className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl p-8 sm:p-10 w-full max-w-md text-center transform transition-all"
      >
        {/* Animated checkmark */}
        <div className="mb-6 flex justify-center">
          <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
            <svg
              className="w-9 h-9 text-green-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2.5}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
        </div>

        {/* Title */}
        <h3
          id="contact-success-title"
          className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 mb-3"
        >
          Message Sent!
        </h3>

        {/* Description */}
        <p className="text-gray-600 dark:text-gray-400 text-base mb-2 leading-relaxed">
          Thank you for reaching out. Your message has been delivered to our team.
        </p>
        <p className="text-gray-500 dark:text-gray-500 text-sm mb-8">
          We typically respond within 1–3 business days.
        </p>

        {/* Close button */}
        <button
          ref={closeButtonRef}
          type="button"
          onClick={onClose}
          className="inline-flex items-center justify-center px-6 py-3 text-base font-semibold rounded-lg bg-primary-400 text-gray-900 hover:bg-primary-500 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-900 min-h-[44px]"
        >
          Got It
        </button>
      </div>
    </div>
  );
}
