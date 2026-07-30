'use client';

import React, { useState } from 'react';
import {
  SponsorshipOpportunityType,
  BudgetRange,
  OPPORTUNITY_OPTIONS,
  BUDGET_OPTIONS,
} from '@/lib/data/sponsorship-data';
import { Button } from '@/components/ui/Button';

export interface SponsorshipFormData {
  fullName: string;
  email: string;
  company: string;
  jobTitle: string;
  website: string;
  opportunityType: SponsorshipOpportunityType | '';
  budgetRange: BudgetRange | '';
  timeline: string;
  goals: string;
  additionalDetails: string;
}

export interface SponsorshipInquiryFormProps {
  onSubmit?: (data: SponsorshipFormData) => Promise<{ success: boolean; error?: string }>;
  className?: string;
}

interface FormErrors {
  fullName?: string;
  email?: string;
  company?: string;
  jobTitle?: string;
  website?: string;
  opportunityType?: string;
  budgetRange?: string;
  timeline?: string;
  goals?: string;
  additionalDetails?: string;
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const defaultOnSubmit = async (): Promise<{ success: boolean; error?: string }> => {
  return { success: false, error: 'Submission endpoint not configured. Please contact info@devsecblueprint.com directly.' };
};

/**
 * SponsorshipInquiryForm component with client-side validation, accessible labels,
 * inline error messages, and confirmation state on successful submission.
 *
 * @param onSubmit - Optional async handler invoked with validated form data.
 *                   Defaults to a placeholder that returns a configuration error.
 * @param className - Additional CSS classes for the form wrapper.
 */
export function SponsorshipInquiryForm({ onSubmit = defaultOnSubmit, className = '' }: SponsorshipInquiryFormProps) {
  const [formData, setFormData] = useState<SponsorshipFormData>({
    fullName: '',
    email: '',
    company: '',
    jobTitle: '',
    website: '',
    opportunityType: '' as SponsorshipOpportunityType,
    budgetRange: '' as BudgetRange,
    timeline: '',
    goals: '',
    additionalDetails: '',
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  function validate(data: SponsorshipFormData): FormErrors {
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

    // Company: required, 1–100 chars
    if (!data.company.trim()) {
      errs.company = 'This field is required';
    } else if (data.company.length > 100) {
      errs.company = 'Maximum 100 characters allowed';
    }

    // Job Title: optional, 0–100 chars
    if (data.jobTitle.length > 100) {
      errs.jobTitle = 'Maximum 100 characters allowed';
    }

    // Website: optional, 0–200 chars, must start with http:// or https:// if non-empty
    if (data.website.trim()) {
      if (data.website.length > 200) {
        errs.website = 'Maximum 200 characters allowed';
      } else if (!data.website.startsWith('http://') && !data.website.startsWith('https://')) {
        errs.website = 'URL must start with http:// or https://';
      }
    }

    // Opportunity Type: required
    if (!data.opportunityType) {
      errs.opportunityType = 'This field is required';
    }

    // Budget Range: required
    if (!data.budgetRange) {
      errs.budgetRange = 'This field is required';
    }

    // Timeline: optional, 0–200 chars
    if (data.timeline.length > 200) {
      errs.timeline = 'Maximum 200 characters allowed';
    }

    // Goals: required, 10–1000 chars
    if (!data.goals.trim()) {
      errs.goals = 'This field is required';
    } else if (data.goals.trim().length < 10) {
      errs.goals = 'Goals must be at least 10 characters';
    } else if (data.goals.length > 1000) {
      errs.goals = 'Maximum 1000 characters allowed';
    }

    // Additional Details: optional, 0–2000 chars
    if (data.additionalDetails.length > 2000) {
      errs.additionalDetails = 'Maximum 2000 characters allowed';
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
          Inquiry Submitted Successfully
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          Thank you for your interest in sponsoring The DevSec Blueprint. Our team will review your inquiry and respond within 5 business days.
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
          htmlFor="sponsorship-fullName"
          className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1"
        >
          Full Name <span aria-hidden="true">*</span>
        </label>
        <input
          type="text"
          id="sponsorship-fullName"
          name="fullName"
          value={formData.fullName}
          onChange={handleChange}
          aria-required="true"
          aria-describedby={errors.fullName ? 'sponsorship-fullName-error' : undefined}
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
          <p id="sponsorship-fullName-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
            {errors.fullName}
          </p>
        )}
      </div>

      {/* Email */}
      <div>
        <label
          htmlFor="sponsorship-email"
          className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1"
        >
          Work Email <span aria-hidden="true">*</span>
        </label>
        <input
          type="email"
          id="sponsorship-email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          aria-required="true"
          aria-describedby={errors.email ? 'sponsorship-email-error' : undefined}
          aria-invalid={!!errors.email}
          className={`w-full rounded-lg border px-4 py-3 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent ${
            errors.email
              ? 'border-red-500 dark:border-red-400'
              : 'border-gray-300 dark:border-gray-700'
          }`}
          placeholder="name@company.com"
          maxLength={254}
        />
        {errors.email && (
          <p id="sponsorship-email-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
            {errors.email}
          </p>
        )}
      </div>

      {/* Company */}
      <div>
        <label
          htmlFor="sponsorship-company"
          className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1"
        >
          Company / Organization <span aria-hidden="true">*</span>
        </label>
        <input
          type="text"
          id="sponsorship-company"
          name="company"
          value={formData.company}
          onChange={handleChange}
          aria-required="true"
          aria-describedby={errors.company ? 'sponsorship-company-error' : undefined}
          aria-invalid={!!errors.company}
          className={`w-full rounded-lg border px-4 py-3 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent ${
            errors.company
              ? 'border-red-500 dark:border-red-400'
              : 'border-gray-300 dark:border-gray-700'
          }`}
          placeholder="Your company or organization"
          maxLength={100}
        />
        {errors.company && (
          <p id="sponsorship-company-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
            {errors.company}
          </p>
        )}
      </div>

      {/* Job Title (optional) */}
      <div>
        <label
          htmlFor="sponsorship-jobTitle"
          className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1"
        >
          Job Title <span className="text-gray-500 dark:text-gray-400 font-normal">(optional)</span>
        </label>
        <input
          type="text"
          id="sponsorship-jobTitle"
          name="jobTitle"
          value={formData.jobTitle}
          onChange={handleChange}
          aria-describedby={errors.jobTitle ? 'sponsorship-jobTitle-error' : undefined}
          aria-invalid={!!errors.jobTitle}
          className={`w-full rounded-lg border px-4 py-3 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent ${
            errors.jobTitle
              ? 'border-red-500 dark:border-red-400'
              : 'border-gray-300 dark:border-gray-700'
          }`}
          placeholder="Your job title"
          maxLength={100}
        />
        {errors.jobTitle && (
          <p id="sponsorship-jobTitle-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
            {errors.jobTitle}
          </p>
        )}
      </div>

      {/* Company Website (optional) */}
      <div>
        <label
          htmlFor="sponsorship-website"
          className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1"
        >
          Company Website <span className="text-gray-500 dark:text-gray-400 font-normal">(optional)</span>
        </label>
        <input
          type="url"
          id="sponsorship-website"
          name="website"
          value={formData.website}
          onChange={handleChange}
          aria-describedby={errors.website ? 'sponsorship-website-error' : undefined}
          aria-invalid={!!errors.website}
          className={`w-full rounded-lg border px-4 py-3 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent ${
            errors.website
              ? 'border-red-500 dark:border-red-400'
              : 'border-gray-300 dark:border-gray-700'
          }`}
          placeholder="https://company.com"
          maxLength={200}
        />
        {errors.website && (
          <p id="sponsorship-website-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
            {errors.website}
          </p>
        )}
      </div>

      {/* Sponsorship Opportunity Type */}
      <div>
        <label
          htmlFor="sponsorship-opportunityType"
          className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1"
        >
          Sponsorship Opportunity <span aria-hidden="true">*</span>
        </label>
        <select
          id="sponsorship-opportunityType"
          name="opportunityType"
          value={formData.opportunityType}
          onChange={handleChange}
          aria-required="true"
          aria-describedby={errors.opportunityType ? 'sponsorship-opportunityType-error' : undefined}
          aria-invalid={!!errors.opportunityType}
          className={`w-full rounded-lg border px-4 py-3 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent ${
            errors.opportunityType
              ? 'border-red-500 dark:border-red-400'
              : 'border-gray-300 dark:border-gray-700'
          }`}
        >
          <option value="">Select a sponsorship opportunity</option>
          {OPPORTUNITY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {errors.opportunityType && (
          <p id="sponsorship-opportunityType-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
            {errors.opportunityType}
          </p>
        )}
      </div>

      {/* Budget Range */}
      <div>
        <label
          htmlFor="sponsorship-budgetRange"
          className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1"
        >
          Estimated Budget Range <span aria-hidden="true">*</span>
        </label>
        <select
          id="sponsorship-budgetRange"
          name="budgetRange"
          value={formData.budgetRange}
          onChange={handleChange}
          aria-required="true"
          aria-describedby={errors.budgetRange ? 'sponsorship-budgetRange-error' : undefined}
          aria-invalid={!!errors.budgetRange}
          className={`w-full rounded-lg border px-4 py-3 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent ${
            errors.budgetRange
              ? 'border-red-500 dark:border-red-400'
              : 'border-gray-300 dark:border-gray-700'
          }`}
        >
          <option value="">Select a budget range</option>
          {BUDGET_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {errors.budgetRange && (
          <p id="sponsorship-budgetRange-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
            {errors.budgetRange}
          </p>
        )}
      </div>

      {/* Timeline (optional) */}
      <div>
        <label
          htmlFor="sponsorship-timeline"
          className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1"
        >
          Desired Timeline <span className="text-gray-500 dark:text-gray-400 font-normal">(optional)</span>
        </label>
        <input
          type="text"
          id="sponsorship-timeline"
          name="timeline"
          value={formData.timeline}
          onChange={handleChange}
          aria-describedby={errors.timeline ? 'sponsorship-timeline-error' : undefined}
          aria-invalid={!!errors.timeline}
          className={`w-full rounded-lg border px-4 py-3 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent ${
            errors.timeline
              ? 'border-red-500 dark:border-red-400'
              : 'border-gray-300 dark:border-gray-700'
          }`}
          placeholder="e.g., Q1 2025, Immediate, Within 3 months"
          maxLength={200}
        />
        {errors.timeline && (
          <p id="sponsorship-timeline-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
            {errors.timeline}
          </p>
        )}
      </div>

      {/* Partnership Goals */}
      <div>
        <label
          htmlFor="sponsorship-goals"
          className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1"
        >
          Partnership Goals <span aria-hidden="true">*</span>
        </label>
        <textarea
          id="sponsorship-goals"
          name="goals"
          value={formData.goals}
          onChange={handleChange}
          aria-required="true"
          aria-describedby={errors.goals ? 'sponsorship-goals-error' : undefined}
          aria-invalid={!!errors.goals}
          rows={4}
          className={`w-full rounded-lg border px-4 py-3 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent resize-y ${
            errors.goals
              ? 'border-red-500 dark:border-red-400'
              : 'border-gray-300 dark:border-gray-700'
          }`}
          placeholder="Describe your sponsorship goals and what you hope to achieve (minimum 10 characters)"
          maxLength={1000}
        />
        {errors.goals && (
          <p id="sponsorship-goals-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
            {errors.goals}
          </p>
        )}
      </div>

      {/* Additional Details (optional) */}
      <div>
        <label
          htmlFor="sponsorship-additionalDetails"
          className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1"
        >
          Additional Details <span className="text-gray-500 dark:text-gray-400 font-normal">(optional)</span>
        </label>
        <textarea
          id="sponsorship-additionalDetails"
          name="additionalDetails"
          value={formData.additionalDetails}
          onChange={handleChange}
          aria-describedby={errors.additionalDetails ? 'sponsorship-additionalDetails-error' : undefined}
          aria-invalid={!!errors.additionalDetails}
          rows={4}
          className={`w-full rounded-lg border px-4 py-3 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent resize-y ${
            errors.additionalDetails
              ? 'border-red-500 dark:border-red-400'
              : 'border-gray-300 dark:border-gray-700'
          }`}
          placeholder="Any additional information you'd like to share"
          maxLength={2000}
        />
        {errors.additionalDetails && (
          <p id="sponsorship-additionalDetails-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
            {errors.additionalDetails}
          </p>
        )}
      </div>

      {/* Submit Button */}
      <div>
        <Button
          type="submit"
          variant="primary"
          size="md"
          disabled={isSubmitting}
          className="w-full"
        >
          {isSubmitting ? 'Submitting...' : 'Submit Sponsorship Inquiry'}
        </Button>
      </div>
    </form>
  );
}
