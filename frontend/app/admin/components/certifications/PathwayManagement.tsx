'use client';

import { useEffect, useState, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { Spinner } from '@/components/ui/Spinner';
import { Button } from '@/components/ui/Button';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface PathwayVersion {
  pathway_id: string;
  version: string;
  display_name: string;
  description: string;
  pathway_code: string;
  capstone_content_id: string;
  learning_requirements: string[];
  is_active: boolean;
  created_at: string;
  created_by: string;
}

interface PathwayListItem {
  pathway_id: string;
  pathway_code: string;
  display_name: string;
  current_version: string;
  is_active: boolean;
}

interface CreateVersionForm {
  version: string;
  display_name: string;
  description: string;
  capstone_content_id: string;
  learning_requirements: string;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const EMPTY_FORM: CreateVersionForm = {
  version: '',
  display_name: '',
  description: '',
  capstone_content_id: '',
  learning_requirements: '',
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function PathwayManagement() {
  const [pathways, setPathways] = useState<PathwayListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Which pathway has the "create version" form open
  const [activeFormPathwayId, setActiveFormPathwayId] = useState<string | null>(
    null
  );
  const [formData, setFormData] = useState<CreateVersionForm>(EMPTY_FORM);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Which pathway has the version history expanded
  const [expandedPathwayId, setExpandedPathwayId] = useState<string | null>(
    null
  );
  const [versionHistory, setVersionHistory] = useState<PathwayVersion[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  // ---------------------------------------------------------------------------
  // Fetch pathways
  // ---------------------------------------------------------------------------

  const fetchPathways = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data, error: apiError } = await apiClient.get<PathwayListItem[]>(
        '/admin/certifications/pathways'
      );

      if (apiError) {
        setError(apiError);
        return;
      }
      if (data) {
        setPathways(data);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to fetch pathways'
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPathways();
  }, [fetchPathways]);

  // ---------------------------------------------------------------------------
  // Fetch version history
  // ---------------------------------------------------------------------------

  const fetchVersionHistory = useCallback(async (pathwayId: string) => {
    setIsLoadingHistory(true);
    try {
      const { data, error: apiError } = await apiClient.get<PathwayVersion[]>(
        `/admin/certifications/pathways/${encodeURIComponent(pathwayId)}`
      );

      if (apiError) {
        setVersionHistory([]);
        return;
      }
      if (data) {
        setVersionHistory(data);
      }
    } catch {
      setVersionHistory([]);
    } finally {
      setIsLoadingHistory(false);
    }
  }, []);

  const handleToggleHistory = (pathwayId: string) => {
    if (expandedPathwayId === pathwayId) {
      setExpandedPathwayId(null);
      setVersionHistory([]);
    } else {
      setExpandedPathwayId(pathwayId);
      fetchVersionHistory(pathwayId);
    }
  };

  // ---------------------------------------------------------------------------
  // Create version form
  // ---------------------------------------------------------------------------

  const handleOpenForm = (pathwayId: string) => {
    if (activeFormPathwayId === pathwayId) {
      setActiveFormPathwayId(null);
      setFormData(EMPTY_FORM);
      setSubmitError(null);
    } else {
      setActiveFormPathwayId(pathwayId);
      setFormData(EMPTY_FORM);
      setSubmitError(null);
    }
  };

  const handleFormChange = (
    field: keyof CreateVersionForm,
    value: string
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmitVersion = async (pathwayId: string) => {
    setIsSubmitting(true);
    setSubmitError(null);

    const learningRequirements = formData.learning_requirements
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    try {
      const { error: apiError } = await apiClient.put(
        `/admin/certifications/pathways/${encodeURIComponent(pathwayId)}`,
        {
          version: formData.version,
          display_name: formData.display_name,
          description: formData.description,
          capstone_content_id: formData.capstone_content_id,
          learning_requirements: learningRequirements,
        }
      );

      if (apiError) {
        setSubmitError(apiError);
        return;
      }

      // Success — close form, refresh pathways
      setActiveFormPathwayId(null);
      setFormData(EMPTY_FORM);
      fetchPathways();

      // Refresh history if it was expanded
      if (expandedPathwayId === pathwayId) {
        fetchVersionHistory(pathwayId);
      }
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : 'Failed to create version'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Loading state
  // ---------------------------------------------------------------------------

  if (isLoading) {
    return (
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Pathway Management
        </h3>
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-16 rounded-lg bg-gray-100 dark:bg-gray-800 animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Error state
  // ---------------------------------------------------------------------------

  if (error) {
    return (
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Pathway Management
        </h3>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
          <div className="flex items-start space-x-3">
            <svg
              className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-red-900 dark:text-red-100 mb-1">
                Failed to Load Pathways
              </h4>
              <p className="text-sm text-red-800 dark:text-red-200 mb-3">
                {error}
              </p>
              <button
                onClick={fetchPathways}
                className="text-sm font-medium text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div>
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        Pathway Management
      </h3>

      {pathways.length === 0 && (
        <p className="text-sm text-gray-600 dark:text-gray-400">
          No pathways defined yet.
        </p>
      )}

      <div className="space-y-4">
        {pathways.map((pathway) => (
          <div
            key={pathway.pathway_id}
            className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
          >
            {/* Pathway row */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 bg-gray-50 dark:bg-gray-800">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                    {pathway.display_name}
                  </span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono text-gray-600 dark:text-gray-400 bg-gray-200 dark:bg-gray-700">
                    {pathway.pathway_code}
                  </span>
                  {pathway.is_active && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                      Active
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-500">
                  Version: {pathway.current_version}
                </p>
              </div>

              <div className="flex items-center gap-2 mt-3 sm:mt-0">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleToggleHistory(pathway.pathway_id)}
                  aria-expanded={expandedPathwayId === pathway.pathway_id}
                  aria-label={`Toggle version history for ${pathway.display_name}`}
                >
                  {expandedPathwayId === pathway.pathway_id
                    ? 'Hide History'
                    : 'History'}
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleOpenForm(pathway.pathway_id)}
                  aria-label={`Create new version for ${pathway.display_name}`}
                >
                  {activeFormPathwayId === pathway.pathway_id
                    ? 'Cancel'
                    : 'Create Version'}
                </Button>
              </div>
            </div>

            {/* Create Version Form */}
            {activeFormPathwayId === pathway.pathway_id && (
              <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-900">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  Create New Version
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label
                      htmlFor={`version-${pathway.pathway_id}`}
                      className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
                    >
                      Version
                    </label>
                    <input
                      id={`version-${pathway.pathway_id}`}
                      type="text"
                      placeholder="e.g., 2027.1"
                      value={formData.version}
                      onChange={(e) =>
                        handleFormChange('version', e.target.value)
                      }
                      className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400"
                    />
                  </div>
                  <div>
                    <label
                      htmlFor={`display-name-${pathway.pathway_id}`}
                      className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
                    >
                      Display Name
                    </label>
                    <input
                      id={`display-name-${pathway.pathway_id}`}
                      type="text"
                      placeholder="e.g., DevSecOps Engineering"
                      value={formData.display_name}
                      onChange={(e) =>
                        handleFormChange('display_name', e.target.value)
                      }
                      className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400"
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <label
                      htmlFor={`description-${pathway.pathway_id}`}
                      className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
                    >
                      Description
                    </label>
                    <textarea
                      id={`description-${pathway.pathway_id}`}
                      placeholder="Pathway description..."
                      value={formData.description}
                      onChange={(e) =>
                        handleFormChange('description', e.target.value)
                      }
                      rows={2}
                      className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400 resize-y"
                    />
                  </div>
                  <div>
                    <label
                      htmlFor={`capstone-${pathway.pathway_id}`}
                      className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
                    >
                      Capstone Content ID
                    </label>
                    <input
                      id={`capstone-${pathway.pathway_id}`}
                      type="text"
                      placeholder="Content ID for capstone"
                      value={formData.capstone_content_id}
                      onChange={(e) =>
                        handleFormChange('capstone_content_id', e.target.value)
                      }
                      className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400"
                    />
                  </div>
                  <div>
                    <label
                      htmlFor={`learning-reqs-${pathway.pathway_id}`}
                      className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
                    >
                      Learning Requirements (comma-separated)
                    </label>
                    <input
                      id={`learning-reqs-${pathway.pathway_id}`}
                      type="text"
                      placeholder="content-id-1, content-id-2, ..."
                      value={formData.learning_requirements}
                      onChange={(e) =>
                        handleFormChange(
                          'learning_requirements',
                          e.target.value
                        )
                      }
                      className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400"
                    />
                  </div>
                </div>

                {submitError && (
                  <p className="mt-3 text-sm text-red-600 dark:text-red-400">
                    {submitError}
                  </p>
                )}

                <div className="mt-4 flex justify-end">
                  <Button
                    variant="primary"
                    size="sm"
                    disabled={
                      isSubmitting ||
                      !formData.version.trim() ||
                      !formData.display_name.trim()
                    }
                    onClick={() => handleSubmitVersion(pathway.pathway_id)}
                  >
                    {isSubmitting ? (
                      <span className="flex items-center gap-2">
                        <Spinner size="sm" />
                        Creating...
                      </span>
                    ) : (
                      'Create Version'
                    )}
                  </Button>
                </div>
              </div>
            )}

            {/* Version History */}
            {expandedPathwayId === pathway.pathway_id && (
              <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-900">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  Version History
                </h4>
                {isLoadingHistory ? (
                  <div className="flex items-center justify-center py-4">
                    <Spinner size="sm" />
                  </div>
                ) : versionHistory.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-500">
                    No version history available.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {versionHistory.map((v) => (
                      <div
                        key={`${v.pathway_id}-${v.version}`}
                        className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800"
                      >
                        <div>
                          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            v{v.version}
                          </span>
                          <span className="ml-2 text-xs text-gray-500 dark:text-gray-500">
                            {v.display_name}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          {v.is_active && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                              Active
                            </span>
                          )}
                          <span className="text-xs text-gray-400 dark:text-gray-500">
                            {new Date(v.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
