'use client';

import { useState } from 'react';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ReviewDecision = 'PASSED' | 'REVISIONS_REQUIRED' | 'FAILED';

interface RubricDimension {
  key: string;
  label: string;
  score: string;
  comment: string;
}

interface EvaluationDimension {
  key: string;
  label: string;
  assessment: string;
}

// ---------------------------------------------------------------------------
// Constants — Pre-defined rubric and evaluation dimensions
// ---------------------------------------------------------------------------

const DEFAULT_RUBRIC_DIMENSIONS: { key: string; label: string }[] = [
  { key: 'architecture', label: 'Architecture & Design' },
  { key: 'security', label: 'Security Implementation' },
  { key: 'code_quality', label: 'Code Quality & Best Practices' },
  { key: 'documentation', label: 'Documentation & Clarity' },
  { key: 'completeness', label: 'Project Completeness' },
];

const DEFAULT_EVALUATION_DIMENSIONS: { key: string; label: string }[] = [
  { key: 'technical_depth', label: 'Technical Depth & Understanding' },
  { key: 'problem_solving', label: 'Problem Solving Ability' },
  { key: 'communication', label: 'Communication & Articulation' },
];

const DECISION_OPTIONS: { value: ReviewDecision; label: string; description: string }[] = [
  {
    value: 'PASSED',
    label: 'Passed',
    description: 'Candidate has met all requirements',
  },
  {
    value: 'REVISIONS_REQUIRED',
    label: 'Revisions Required',
    description: 'Candidate must resubmit with improvements',
  },
  {
    value: 'FAILED',
    label: 'Failed',
    description: 'Candidate did not meet requirements',
  },
];

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ReviewOutcomeFormProps {
  userId: string;
  pathwayId: string;
  onComplete: () => void;
  onCancel: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ReviewOutcomeForm({
  userId,
  pathwayId,
  onComplete,
  onCancel,
}: ReviewOutcomeFormProps) {
  // Form state
  const [decision, setDecision] = useState<ReviewDecision | null>(null);
  const [rubricDimensions, setRubricDimensions] = useState<RubricDimension[]>(
    DEFAULT_RUBRIC_DIMENSIONS.map((d) => ({
      ...d,
      score: '',
      comment: '',
    }))
  );
  const [evaluationDimensions, setEvaluationDimensions] = useState<EvaluationDimension[]>(
    DEFAULT_EVALUATION_DIMENSIONS.map((d) => ({
      ...d,
      assessment: '',
    }))
  );
  const [reviewerNotes, setReviewerNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const handleRubricScoreChange = (index: number, score: string) => {
    setRubricDimensions((prev) =>
      prev.map((dim, i) => (i === index ? { ...dim, score } : dim))
    );
  };

  const handleRubricCommentChange = (index: number, comment: string) => {
    setRubricDimensions((prev) =>
      prev.map((dim, i) => (i === index ? { ...dim, comment } : dim))
    );
  };

  const handleEvaluationChange = (index: number, assessment: string) => {
    setEvaluationDimensions((prev) =>
      prev.map((dim, i) => (i === index ? { ...dim, assessment } : dim))
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate decision selected
    if (!decision) {
      setError('Please select a review decision');
      return;
    }

    // Build rubric_scores payload
    const rubricScores: Record<string, { score: string; comment: string }> = {};
    for (const dim of rubricDimensions) {
      if (dim.score || dim.comment) {
        rubricScores[dim.key] = {
          score: dim.score,
          comment: dim.comment,
        };
      }
    }

    // Build evaluation_dimensions payload
    const evalDimensions: Record<string, string> = {};
    for (const dim of evaluationDimensions) {
      if (dim.assessment) {
        evalDimensions[dim.key] = dim.assessment;
      }
    }

    const body = {
      status: decision,
      rubric_scores: rubricScores,
      evaluation_dimensions: evalDimensions,
      reviewer_notes: reviewerNotes,
    };

    setIsSubmitting(true);
    try {
      const { error: apiError } = await apiClient.post(
        `/admin/certifications/candidates/${encodeURIComponent(userId)}/${encodeURIComponent(pathwayId)}/review-outcome`,
        body
      );
      if (apiError) {
        setError(apiError);
        return;
      }
      onComplete();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to submit review outcome'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Form title */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Record Review Outcome
        </h3>
        <button
          type="button"
          onClick={onCancel}
          className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
        >
          Cancel
        </button>
      </div>

      {/* Status Decision */}
      <fieldset className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <legend className="text-sm font-semibold text-gray-700 dark:text-gray-300 px-2">
          Decision
        </legend>
        <div className="space-y-3 mt-2">
          {DECISION_OPTIONS.map((option) => (
            <label
              key={option.value}
              className={`flex items-start space-x-3 rounded-lg border p-3 cursor-pointer transition-colors ${
                decision === option.value
                  ? 'border-amber-400 bg-amber-50 dark:bg-amber-900/10 dark:border-amber-600'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
            >
              <input
                type="radio"
                name="review-decision"
                value={option.value}
                checked={decision === option.value}
                onChange={() => setDecision(option.value)}
                className="mt-0.5 h-4 w-4 text-amber-500 focus:ring-amber-500 border-gray-300 dark:border-gray-600"
              />
              <div>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {option.label}
                </span>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {option.description}
                </p>
              </div>
            </label>
          ))}
        </div>
      </fieldset>

      {/* Rubric Dimensions */}
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">
          Rubric Evaluation
        </h4>
        <div className="space-y-4">
          {rubricDimensions.map((dim, index) => (
            <div
              key={dim.key}
              className="border-b border-gray-100 dark:border-gray-800 pb-4 last:border-0 last:pb-0"
            >
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {dim.label}
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <div className="sm:col-span-1">
                  <input
                    type="text"
                    placeholder="Score (e.g. 8/10)"
                    value={dim.score}
                    onChange={(e) =>
                      handleRubricScoreChange(index, e.target.value)
                    }
                    className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400"
                    aria-label={`Score for ${dim.label}`}
                  />
                </div>
                <div className="sm:col-span-3">
                  <textarea
                    placeholder="Comments..."
                    value={dim.comment}
                    onChange={(e) =>
                      handleRubricCommentChange(index, e.target.value)
                    }
                    rows={2}
                    className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400 resize-none"
                    aria-label={`Comment for ${dim.label}`}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Evaluation Dimensions (Defense Assessment) */}
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">
          Defense Assessment
        </h4>
        <div className="space-y-4">
          {evaluationDimensions.map((dim, index) => (
            <div key={dim.key}>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {dim.label}
              </label>
              <textarea
                placeholder={`Assessment for ${dim.label}...`}
                value={dim.assessment}
                onChange={(e) =>
                  handleEvaluationChange(index, e.target.value)
                }
                rows={3}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400 resize-none"
                aria-label={`Assessment for ${dim.label}`}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Reviewer Notes */}
      <div>
        <label
          htmlFor="reviewer-notes"
          className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2"
        >
          Reviewer Notes
        </label>
        <textarea
          id="reviewer-notes"
          placeholder="Overall notes and feedback for the candidate..."
          value={reviewerNotes}
          onChange={(e) => setReviewerNotes(e.target.value)}
          rows={4}
          className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400 resize-y"
        />
      </div>

      {/* Error message */}
      {error && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-3">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Submit buttons */}
      <div className="flex items-center justify-end space-x-3 pt-2">
        <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
          Cancel
        </Button>
        <Button
          type="submit"
          variant="primary"
          size="sm"
          disabled={isSubmitting || !decision}
        >
          {isSubmitting ? (
            <span className="flex items-center space-x-2">
              <Spinner size="sm" />
              <span>Submitting...</span>
            </span>
          ) : (
            'Submit Review Outcome'
          )}
        </Button>
      </div>
    </form>
  );
}
