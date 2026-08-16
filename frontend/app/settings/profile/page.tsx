'use client';

import { useState, useEffect, useCallback } from 'react';
import { AuthGuard } from '@/components/AuthGuard';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { apiClient } from '@/lib/api';

/**
 * Extended user profile response from GET /user/profile
 * Includes fields needed for the profile settings page display.
 */
interface ProfileData {
  user_id: string;
  username: string;
  avatar_url: string;
  email: string;
  provider: string;
  github_username: string;
  gitlab_username: string;
  bitbucket_username: string;
  registered_at: string;
  last_login: string;
  is_new_user: boolean;
  total_completions: number;
  full_name: string;
}

/**
 * Get a display-friendly label for the OAuth provider.
 */
function getProviderLabel(provider: string): string {
  switch (provider) {
    case 'github':
      return 'GitHub';
    case 'gitlab':
      return 'GitLab';
    case 'bitbucket':
      return 'Bitbucket';
    default:
      return provider;
  }
}

/**
 * Get the provider username from profile data based on the provider type.
 */
function getProviderUsername(profile: ProfileData): string {
  switch (profile.provider) {
    case 'gitlab':
      return profile.gitlab_username || profile.username;
    case 'bitbucket':
      return profile.bitbucket_username || profile.username;
    default:
      return profile.github_username || profile.username;
  }
}

/**
 * Format a date string for display.
 */
function formatDate(dateStr: string): string {
  if (!dateStr) return 'N/A';
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

/**
 * Profile Settings Page
 *
 * Displays read-only account information (avatar, email, provider username,
 * registration date) and an editable full name field. Learners can update
 * their full name which is used on issued certificates.
 */
export default function ProfileSettingsPage() {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [fullName, setFullName] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchProfile = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    const { data, error: apiError } = await apiClient.get<ProfileData>('/user/profile');
    if (apiError) {
      setError(apiError);
    } else if (data) {
      setProfile(data);
      setFullName(data.full_name || '');
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  /**
   * Validate the full name input.
   * Returns an error message or null if valid.
   */
  function validateFullName(value: string): string | null {
    if (!value || value.trim() === '') {
      return 'Full name is required and cannot be empty.';
    }
    if (value.length > 200) {
      return 'Full name must not exceed 200 characters.';
    }
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage(null);
    setError(null);

    // Client-side validation
    const validationErr = validateFullName(fullName);
    if (validationErr) {
      setValidationError(validationErr);
      return;
    }
    setValidationError(null);

    // Submit to API
    setIsSaving(true);
    const { error: apiError } = await apiClient.put<{ full_name: string }>('/user/profile', {
      full_name: fullName.trim(),
    });

    if (apiError) {
      setError(apiError);
    } else {
      setSuccessMessage('Profile updated successfully.');
      // Update the local full name to the trimmed version
      setFullName(fullName.trim());
      if (profile) {
        setProfile({ ...profile, full_name: fullName.trim() });
      }
    }
    setIsSaving(false);
  };

  return (
    <AuthGuard>
      <div className="min-h-screen bg-white dark:bg-gray-950">
        <NavbarWithAuth />
        <main className="pt-16">
          <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              Profile Settings
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mb-8">
              View your account information and manage your display name for certificates.
            </p>

            {/* Error Banner */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
              </div>
            )}

            {/* Success Banner */}
            {successMessage && (
              <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <p className="text-sm text-green-700 dark:text-green-400">{successMessage}</p>
              </div>
            )}

            {isLoading ? (
              /* Loading skeleton */
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6">
                <div className="animate-pulse space-y-6">
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 bg-gray-200 dark:bg-gray-800 rounded-full" />
                    <div className="space-y-2">
                      <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-32" />
                      <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-48" />
                    </div>
                  </div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-56" />
                  <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-40" />
                  <div className="h-10 bg-gray-200 dark:bg-gray-800 rounded w-full" />
                </div>
              </div>
            ) : profile ? (
              <div className="space-y-6">
                {/* Account Information (Read-Only) */}
                <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    Account Information
                  </h2>

                  <div className="space-y-4">
                    {/* Avatar and Username */}
                    <div className="flex items-center gap-4">
                      {profile.avatar_url ? (
                        <img
                          src={profile.avatar_url}
                          alt="Profile avatar"
                          className="w-16 h-16 rounded-full border-2 border-gray-200 dark:border-gray-700"
                        />
                      ) : (
                        <div className="w-16 h-16 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                          <svg className="w-8 h-8 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                        </div>
                      )}
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Avatar</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Managed by your {getProviderLabel(profile.provider)} account
                        </p>
                      </div>
                    </div>

                    {/* Email */}
                    {profile.email && (
                      <div>
                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Email</p>
                        <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">{profile.email}</p>
                      </div>
                    )}

                    {/* Provider Username */}
                    <div>
                      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                        {getProviderLabel(profile.provider)} Username
                      </p>
                      <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                        {getProviderUsername(profile)}
                      </p>
                    </div>

                    {/* Registration Date */}
                    <div>
                      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Member Since</p>
                      <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                        {formatDate(profile.registered_at)}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Editable Full Name */}
                <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
                    Full Name
                  </h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    This name will appear on your issued certificates. Please enter your legal full name.
                  </p>

                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                      <label
                        htmlFor="full_name"
                        className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                      >
                        Full Name
                      </label>
                      <input
                        id="full_name"
                        type="text"
                        value={fullName}
                        onChange={(e) => {
                          setFullName(e.target.value);
                          if (validationError) {
                            setValidationError(validateFullName(e.target.value));
                          }
                        }}
                        onBlur={() => {
                          if (fullName) {
                            setValidationError(validateFullName(fullName));
                          }
                        }}
                        placeholder="Enter your full name"
                        maxLength={200}
                        className={`w-full px-3 py-2 text-sm rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-gray-900 ${
                          validationError
                            ? 'border-red-300 dark:border-red-700 focus:ring-red-500'
                            : 'border-gray-300 dark:border-gray-700 focus:ring-blue-500'
                        } bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500`}
                        aria-invalid={!!validationError}
                        aria-describedby={validationError ? 'full-name-error' : undefined}
                      />
                      {validationError && (
                        <p id="full-name-error" className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
                          {validationError}
                        </p>
                      )}
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        {fullName.length}/200 characters
                      </p>
                    </div>

                    <button
                      type="submit"
                      disabled={isSaving}
                      className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
                    >
                      {isSaving ? (
                        <>
                          <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                          Saving...
                        </>
                      ) : (
                        'Save Changes'
                      )}
                    </button>
                  </form>
                </div>

                {/* Settings Navigation Links */}
                <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    Other Settings
                  </h2>
                  <div className="space-y-2">
                    <a
                      href="/settings/connected-accounts"
                      className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
                    >
                      <div className="flex items-center gap-3">
                        <svg className="w-5 h-5 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                        </svg>
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Connected Accounts</span>
                      </div>
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </a>
                    <a
                      href="/settings/subscription"
                      className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
                    >
                      <div className="flex items-center gap-3">
                        <svg className="w-5 h-5 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                        </svg>
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Subscription</span>
                      </div>
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </a>
                  </div>
                </div>
              </div>
            ) : (
              /* No profile loaded */
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Unable to load profile information. Please try again later.
                </p>
              </div>
            )}
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
