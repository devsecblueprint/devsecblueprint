'use client';

import React, { useState } from 'react';
import {
  InquiryType,
  ContactFormData,
  INQUIRY_CATEGORIES,
  INQUIRY_HELPER_TEXT,
} from '@/lib/data/contact';

export interface ContactFormProps {
  onSubmit?: (data: ContactFormData) => Promise<{ success: boolean; error?: string }>;
  className?: string;
}

interface FormErrors {
  fullName?: string;
  email?: string;
  organization?: string;
  inquiryType?: string;
  subject?: string;
  message?: string;
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const defaultOnSubmit = async (): Promise<{ success: boolean; error?: string }> => {
  return { success: true };
};

/**
 * ContactForm component with client-side validation, accessible labels,
 * inline error messages, and confirmation state on successful submission.
 *
 * @param onSubmit - Optional async handler invoked with validated form data.
 *                   Defaults to a placeholder that resolves { success: true }.
 * @param className - Additional CSS classes for the form wrapper.
 */
export function ContactForm({ onSubmit = defaultOnSubmit, className = '' }: ContactFormProps) {
  const [formData, setFormData] = useState<ContactFormData>({
    fullName: '',
    email: '',
    organization: '',
    inquiryType: '' as InquiryType,
    subject: '',
    message: '',
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  function validate(data: ContactFormData): FormErrors {
    const errs: FormErrors = {};

    // Full Name: required, 1–100 chars
    if (!data.fullName.trim()) {
      errs.fullName = 'This field is required';
    } else if (data.fullName.length > 100) {
      errs.fullName = 'Maximum 100 characters allowed';
    }

    // Email: required, 1–254 chars, email pattern
    if (!data.email.trim()) {
      errs.email = 'This field is required';
    } else if (data.email.length > 254) {
      errs.email = 'Maximum 254 characters allowed';
    } else if (!EMAIL_PATTERN.test(data.email)) {
      errs.email = 'Please enter a valid email address (e.g., name@example.com)';
    }

    // Organization: optional, 0–100 chars
    if (data.organization.length > 100) {
      errs.organization = 'Maximum 100 characters allowed';
    }

    // Inquiry Type: required
    if (!data.inquiryType) {
      errs.inquiryType = 'This field is required';
    }

    // Subject: required, 1–150 chars
    if (!data.subject.trim()) {
      errs.subject = 'This field is required';
    } else if (data.subject.length > 150) {
      errs.subject = 'Maximum 150 characters allowed';
    }

    // Message: required, 10–2000 chars
    if (!data.message.trim()) {
      errs.message = 'This field is required';
    } else if (data.message.trim().length < 10) {
      errs.message = 'Message must be at least 10 characters';
    } else if (data.message.length > 2000) {
      errs.message = 'Maximum 2000 characters allowed';
    }

    return errs;
  }

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear the error for this field on change
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitError(null);

    const validationErrors = validate(formData);
    setErrors(validationErrors);

    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await onSubmit(formData);
      if (result.success) {
        setIsConfirmed(true);
      } else {
        setSubmitError(result.error || 'Submission failed. Please try again.');
      }
    } catch {
      setSubmitError('An unexpected error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  // Confirmation state
  if (isConfirmed) {
    return (
      <div className={`rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-8 text-center ${className}`}>
        <div className="mb-4">
          <svg
            className="mx-auto h-12 w-12 text-green-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
        <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
          Message Sent Successfully
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          Thank you for reaching out. Our team typically responds within 3 business days.
        </p>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={`space-y-6 ${className}`}
      noValidate
    >
      {submitError && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 text-red-700 dark:text-red-400 text-sm" role="alert">
          {submitError}
        </div>
      )}

      {/* Full Name */}
      <div>
        <label
          htmlFor="contact-fullName"
          className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1"
        >
          Full Name <span aria-hidden="true">*</span>
        </label>
        <input
          type="text"
          id="contact-fullName"
          name="fullName"
          value={formData.fullName}
          onChange={handleChange}
          aria-required="true"
          aria-describedby={errors.fullName ? 'contact-fullName-error' : undefined}
          aria-invalid={!!errors.fullName}
          className={`w-full rounded-lg border px-4 py-3 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent ${
            errors.fullName
              ? 'border-red-500 dark:border-red-400'
              : 'border-gray-300 dark:border-gray-700'
          }`}
          placeholder="Your full name"
          maxLength={100}
        />
        {errors.fullName && (
          <p id="contact-fullName-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
            {errors.fullName}
          </p>
        )}
      </div>

      {/* Email */}
      <div>
        <label
          htmlFor="contact-email"
          className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1"
        >
          Email <span aria-hidden="true">*</span>
        </label>
        <input
          type="email"
          id="contact-email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          aria-required="true"
          aria-describedby={errors.email ? 'contact-email-error' : undefined}
          aria-invalid={!!errors.email}
          className={`w-full rounded-lg border px-4 py-3 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent ${
            errors.email
              ? 'border-red-500 dark:border-red-400'
              : 'border-gray-300 dark:border-gray-700'
          }`}
          placeholder="name@example.com"
          maxLength={254}
        />
        {errors.email && (
          <p id="contact-email-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
            {errors.email}
          </p>
        )}
      </div>

      {/* Organization (optional) */}
      <div>
        <label
          htmlFor="contact-organization"
          className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1"
        >
          Organization <span className="text-gray-500 dark:text-gray-400 font-normal">(optional)</span>
        </label>
        <input
          type="text"
          id="contact-organization"
          name="organization"
          value={formData.organization}
          onChange={handleChange}
          aria-describedby={errors.organization ? 'contact-organization-error' : undefined}
          aria-invalid={!!errors.organization}
          className={`w-full rounded-lg border px-4 py-3 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent ${
            errors.organization
              ? 'border-red-500 dark:border-red-400'
              : 'border-gray-300 dark:border-gray-700'
          }`}
          placeholder="Your company or organization"
          maxLength={100}
        />
        {errors.organization && (
          <p id="contact-organization-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
            {errors.organization}
          </p>
        )}
      </div>

      {/* Inquiry Type */}
      <div>
        <label
          htmlFor="contact-inquiryType"
          className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1"
        >
          Inquiry Type <span aria-hidden="true">*</span>
        </label>
        <select
          id="contact-inquiryType"
          name="inquiryType"
          value={formData.inquiryType}
          onChange={handleChange}
          aria-required="true"
          aria-describedby={
            errors.inquiryType
              ? 'contact-inquiryType-error'
              : formData.inquiryType
              ? 'contact-inquiryType-helper'
              : undefined
          }
          aria-invalid={!!errors.inquiryType}
          className={`w-full rounded-lg border px-4 py-3 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent ${
            errors.inquiryType
              ? 'border-red-500 dark:border-red-400'
              : 'border-gray-300 dark:border-gray-700'
          }`}
        >
          <option value="">Select an inquiry type</option>
          {INQUIRY_CATEGORIES.map((cat) => (
            <option key={cat.type} value={cat.type}>
              {cat.label}
            </option>
          ))}
        </select>
        {errors.inquiryType && (
          <p id="contact-inquiryType-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
            {errors.inquiryType}
          </p>
        )}
        {!errors.inquiryType && formData.inquiryType && (
          <p id="contact-inquiryType-helper" className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {INQUIRY_HELPER_TEXT[formData.inquiryType]}
          </p>
        )}
      </div>

      {/* Subject */}
      <div>
        <label
          htmlFor="contact-subject"
          className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1"
        >
          Subject <span aria-hidden="true">*</span>
        </label>
        <input
          type="text"
          id="contact-subject"
          name="subject"
          value={formData.subject}
          onChange={handleChange}
          aria-required="true"
          aria-describedby={errors.subject ? 'contact-subject-error' : undefined}
          aria-invalid={!!errors.subject}
          className={`w-full rounded-lg border px-4 py-3 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent ${
            errors.subject
              ? 'border-red-500 dark:border-red-400'
              : 'border-gray-300 dark:border-gray-700'
          }`}
          placeholder="Brief description of your inquiry"
          maxLength={150}
        />
        {errors.subject && (
          <p id="contact-subject-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
            {errors.subject}
          </p>
        )}
      </div>

      {/* Message */}
      <div>
        <label
          htmlFor="contact-message"
          className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1"
        >
          Message <span aria-hidden="true">*</span>
        </label>
        <textarea
          id="contact-message"
          name="message"
          value={formData.message}
          onChange={handleChange}
          aria-required="true"
          aria-describedby={errors.message ? 'contact-message-error' : undefined}
          aria-invalid={!!errors.message}
          rows={6}
          className={`w-full rounded-lg border px-4 py-3 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent resize-y ${
            errors.message
              ? 'border-red-500 dark:border-red-400'
              : 'border-gray-300 dark:border-gray-700'
          }`}
          placeholder="Please provide details about your inquiry (minimum 10 characters)"
          maxLength={2000}
        />
        {errors.message && (
          <p id="contact-message-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
            {errors.message}
          </p>
        )}
      </div>

      {/* Submit Button */}
      <div>
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-lg bg-primary-400 text-gray-900 font-semibold px-6 py-3 text-base min-h-[44px] hover:bg-primary-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-950 focus:ring-primary-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? 'Sending...' : 'Send Message'}
        </button>
      </div>
    </form>
  );
}
