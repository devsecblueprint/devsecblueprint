'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/hooks/useAuth';
import { validateRepoUrl } from '@/lib/validation';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import MarkdownRenderer from '@/components/MarkdownRenderer';
import type { ReviewData } from '@/lib/types';

export interface CapstoneSubmissionFormProps {
  contentId: string;
  onSubmitSuccess?: () => void;
}

/**
 * CapstoneSubmissionForm Component
 * 
 * Provides UI for learners to submit their GitHub repository URL for capstone projects.
 * Validates that the repository belongs to the authenticated user and handles submission.
 * 
 * Supports three states based on submission status:
 * - pending_review: Read-only display with review timeline message
 * - reviewed: Rendered markdown feedback with download and resubmit options
 * - No status / legacy: Original submission/update behavior
 * 
 * @param contentId - The capstone content ID
 * @param onSubmitSuccess - Optional callback after successful submission
 */
export function CapstoneSubmissionForm({ contentId, onSubmitSuccess }: CapstoneSubmissionFormProps) {
  const { username, providerUsername, provider, isAuthenticated } = useAuth();
  const [repoUrl, setRepoUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submittedUrl, setSubmittedUrl] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [submissionStatus, setSubmissionStatus] = useState<string | null>(null);
  const [reviewData, setReviewData] = useState<ReviewData | null>(null);

  // If not authenticated, don't render the form
  if (!isAuthenticated || !providerUsername) {
    return null;
  }

  const providerDomain = provider === 'gitlab' ? 'gitlab' : provider === 'bitbucket' ? 'bitbucket' : 'github';
  const providerTld = provider === 'bitbucket' ? 'org' : 'com';
  const placeholder = `https://${providerDomain}.${providerTld}/${providerUsername}/project-name`;

  // Fetch existing submission on mount
  useEffect(() => {
    const fetchSubmission = async () => {
      setIsLoading(true);
      const { data, error: fetchError } = await apiClient.getCapstoneSubmission(contentId);
      
      if (data && data.repo_url) {
        setSubmittedUrl(data.repo_url);
        setSubmissionStatus(data.status || null);

        // If reviewed, fetch the review data
        if (data.status === 'reviewed') {
          const { data: reviewResponse } = await apiClient.getCapstoneReview(contentId);
          if (reviewResponse && reviewResponse.review) {
            setReviewData(reviewResponse.review);
          }
        }
      }
      
      setIsLoading(false);
    };

    if (isAuthenticated && providerUsername) {
      fetchSubmission();
    }
  }, [contentId, isAuthenticated, providerUsername]);

  // Validate URL on input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setRepoUrl(value);
    
    // Clear error when user starts typing
    if (error) {
      setError(null);
    }
    
    // Validate if there's a value
    if (value.trim()) {
      const validation = validateRepoUrl(value.trim(), (provider as "github" | "gitlab" | "bitbucket") ?? "github", providerUsername);
      if (!validation.valid) {
        setError(validation.error || 'Invalid URL');
      }
    }
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const trimmedUrl = repoUrl.trim();
    
    // Validate before submission
    if (!trimmedUrl) {
      setError('Please enter a repository URL');
      return;
    }
    
    const validation = validateRepoUrl(trimmedUrl, (provider as "github" | "gitlab" | "bitbucket") ?? "github", providerUsername);
    if (!validation.valid) {
      setError(validation.error || 'Invalid URL');
      return;
    }
    
    // Submit to API
    setIsSubmitting(true);
    setError(null);
    
    try {
      const { data, error: apiError, statusCode } = await apiClient.saveProgress(contentId, trimmedUrl);
      
      if (statusCode === 409) {
        setError('Your submission is currently under review and cannot be updated');
        setIsSubmitting(false);
        return;
      }

      if (apiError) {
        setError(apiError);
        setIsSubmitting(false);
        return;
      }
      
      // Success!
      setSubmittedUrl(trimmedUrl);
      setSubmissionStatus('pending_review');
      setIsEditing(false);
      setIsSubmitting(false);
      
      // Mark capstone as complete (force it since it's a submission)
      if (typeof window !== 'undefined' && (window as any).__markPageComplete) {
        (window as any).__markPageComplete(true);
      }
      
      // Call success callback if provided
      if (onSubmitSuccess) {
        onSubmitSuccess();
      }
    } catch (err) {
      setError('An unexpected error occurred. Please try again.');
      setIsSubmitting(false);
    }
  };

  // Handle update/resubmit button click
  const handleUpdate = () => {
    setIsEditing(true);
    setRepoUrl(submittedUrl || '');
    setError(null);
  };

  // Handle download feedback as .md file
  const handleDownloadFeedback = () => {
    if (!reviewData) return;

    const blob = new Blob([reviewData.feedback], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `capstone-feedback-${contentId}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Show loading state while fetching
  if (isLoading) {
    return (
      <Card className="mt-8">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
        </div>
      </Card>
    );
  }

  // pending_review state: read-only display with review timeline message
  if (submittedUrl && submissionStatus === 'pending_review' && !isEditing) {
    return (
      <Card className="mt-8">
        <div className="space-y-4">
          <div className="flex items-center space-x-2 text-amber-600 dark:text-amber-400">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-lg font-semibold">Project submitted — under review</h3>
          </div>
          
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Submitted repository:</p>
            <a 
              href={submittedUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-amber-500 dark:text-amber-400 hover:text-amber-600 dark:hover:text-amber-300 break-all"
            >
              {submittedUrl}
            </a>
          </div>

          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
            <p className="text-sm text-amber-800 dark:text-amber-200">
              Thank you for your submission. Your project will be reviewed within 7-10 business days and feedback will be sent via email.
            </p>
          </div>
        </div>
      </Card>
    );
  }

  // reviewed state: rendered feedback with download and resubmit options
  if (submittedUrl && submissionStatus === 'reviewed' && !isEditing) {
    return (
      <Card className="mt-8">
        <div className="space-y-4">
          <div className="flex items-center space-x-2 text-green-600 dark:text-green-400">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-lg font-semibold">Review Complete</h3>
          </div>

          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Submitted repository:</p>
            <a 
              href={submittedUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-amber-500 dark:text-amber-400 hover:text-amber-600 dark:hover:text-amber-300 break-all"
            >
              {submittedUrl}
            </a>
          </div>

          {reviewData && (
            <>
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Feedback</h4>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Reviewed by {reviewData.reviewed_by} on{' '}
                    {new Date(reviewData.reviewed_at).toLocaleDateString(undefined, {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </div>
                </div>
                <MarkdownRenderer markdown={reviewData.feedback} />
              </div>

              <div className="flex flex-wrap gap-3">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleDownloadFeedback}
                >
                  Download Feedback
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleUpdate}
                >
                  Resubmit
                </Button>
              </div>
            </>
          )}

          {!reviewData && (
            <Button
              variant="primary"
              size="sm"
              onClick={handleUpdate}
            >
              Resubmit
            </Button>
          )}
        </div>
      </Card>
    );
  }

  // If already submitted with no status (legacy) and not editing, show success state
  if (submittedUrl && !submissionStatus && !isEditing) {
    return (
      <Card className="mt-8">
        <div className="space-y-4">
          <div className="flex items-center space-x-2 text-green-600 dark:text-green-400">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-lg font-semibold">Project submitted successfully!</h3>
          </div>
          
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Submitted repository:</p>
            <a 
              href={submittedUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-amber-500 dark:text-amber-400 hover:text-amber-600 dark:hover:text-amber-300 break-all"
            >
              {submittedUrl}
            </a>
          </div>
          
          <Button
            variant="secondary"
            size="sm"
            onClick={handleUpdate}
            className="w-full sm:w-auto"
          >
            Update Submission
          </Button>
        </div>
      </Card>
    );
  }

  // Show submission form (for new submissions, editing, or resubmission)
  return (
    <Card className="mt-8">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            {submissionStatus === 'reviewed' ? 'Resubmit Your Project' : 'Submit Your Project'}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Enter your repository URL to {submissionStatus === 'reviewed' ? 'resubmit' : 'complete'} the capstone project.
          </p>
        </div>
        
        <div>
          <label htmlFor="repo-url" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Repository URL
          </label>
          <input
            id="repo-url"
            type="text"
            value={repoUrl}
            onChange={handleInputChange}
            placeholder={placeholder}
            disabled={isSubmitting}
            className={`w-full px-4 py-3 rounded-lg border ${
              error 
                ? 'border-red-500 dark:border-red-500' 
                : 'border-gray-300 dark:border-gray-700'
            } bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed`}
          />
          {error && (
            <p className="mt-2 text-sm text-red-600 dark:text-red-400">
              {error}
            </p>
          )}
        </div>
        
        <Button
          type="submit"
          variant="primary"
          size="md"
          disabled={isSubmitting}
          className="w-full sm:w-auto"
        >
          {isSubmitting ? 'Submitting...' : submittedUrl ? 'Update Project' : 'Submit Project'}
        </Button>
      </form>
    </Card>
  );
}
