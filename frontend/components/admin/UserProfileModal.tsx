'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { apiClient, AdminUserProfileResponse } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { format } from 'date-fns';

interface UserProfileModalProps {
  userId: string;
  onClose: () => void;
}

export function UserProfileModal({ userId, onClose }: UserProfileModalProps) {
  const [profile, setProfile] = useState<AdminUserProfileResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Animate in
  useEffect(() => {
    setTimeout(() => setIsVisible(true), 10);
  }, []);

  // Focus management
  useEffect(() => {
    previousFocusRef.current = document.activeElement as HTMLElement;
    const closeBtn = modalRef.current?.querySelector<HTMLElement>('button');
    closeBtn?.focus();
    return () => {
      previousFocusRef.current?.focus();
    };
  }, []);

  // Prevent body scroll
  useEffect(() => {
    const original = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = original;
    };
  }, []);

  // Keyboard handling (Escape to close + focus trap)
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
        'button:not([disabled]), [href], [tabindex]:not([tabindex="-1"])'
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

  // Fetch user profile
  useEffect(() => {
    fetchProfile();
  }, [userId]);

  const fetchProfile = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data, error: apiError } = await apiClient.getAdminUserProfile(userId);
      if (apiError) {
        setError(apiError);
        return;
      }
      if (data) {
        setProfile(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch user profile');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return 'N/A';
    try {
      return format(new Date(dateStr), 'MMM d, yyyy');
    } catch {
      return 'N/A';
    }
  };

  const providerLabel = profile?.user.provider === 'gitlab' ? 'GitLab' : 'GitHub';
  const providerUsername =
    profile?.user.provider === 'gitlab'
      ? profile?.user.gitlab_username
      : profile?.user.github_username;

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-opacity duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
      role="dialog"
      aria-modal="true"
      aria-labelledby="user-profile-title"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div
        ref={modalRef}
        className={`relative w-full max-w-2xl max-h-[85vh] flex flex-col transform transition-all duration-300 ${
          isVisible ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        }`}
      >
        <Card padding="lg">
          {/* Header with close button */}
          <div className="flex items-center justify-between mb-6">
            <h2
              id="user-profile-title"
              className="text-xl font-semibold text-gray-900 dark:text-gray-100"
            >
              User Profile
            </h2>
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

          {/* Content */}
          <div className="overflow-y-auto max-h-[65vh]">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Spinner size="lg" />
              </div>
            ) : error ? (
              <div className="text-center py-8">
                <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
                <Button variant="ghost" onClick={fetchProfile}>
                  Retry
                </Button>
              </div>
            ) : profile ? (
              <div className="space-y-6">
                {/* User info header */}
                <div className="flex items-center space-x-4">
                  {profile.user.avatar_url ? (
                    <img
                      src={profile.user.avatar_url}
                      alt={`${profile.user.username}'s avatar`}
                      className="w-16 h-16 rounded-full"
                    />
                  ) : (
                    <div className="w-16 h-16 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                      <span className="text-2xl text-gray-500 dark:text-gray-400">
                        {profile.user.username?.charAt(0)?.toUpperCase() || '?'}
                      </span>
                    </div>
                  )}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {profile.user.username}
                    </h3>
                    <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                      <span>@{providerUsername || 'unknown'}</span>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          profile.user.provider === 'gitlab'
                            ? 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400'
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
                        }`}
                      >
                        {providerLabel}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Info row: registered date, last login */}
                <div className="flex space-x-6 text-sm text-gray-600 dark:text-gray-400">
                  <div>
                    <span className="font-medium text-gray-700 dark:text-gray-300">Registered:</span>{' '}
                    {formatDate(profile.user.registered_at)}
                  </div>
                  <div>
                    <span className="font-medium text-gray-700 dark:text-gray-300">Last Login:</span>{' '}
                    {formatDate(profile.user.last_login)}
                  </div>
                </div>

                {/* Stats grid (2x3) */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                    Statistics
                  </h4>
                  <div className="grid grid-cols-3 gap-3">
                    <StatCard label="Lessons" value={profile.stats.completed_count} />
                    <StatCard label="Walkthroughs" value={profile.stats.walkthroughs_completed} />
                    <StatCard label="Quizzes" value={profile.stats.quizzes_passed} />
                    <StatCard label="Badges" value={profile.badges.filter((b) => b.earned).length} />
                    <StatCard label="Capstones" value={profile.stats.capstone_submissions} />
                    <StatCard
                      label="Completion"
                      value={`${profile.stats.overall_completion}%`}
                      highlight
                    />
                  </div>
                </div>

                {/* Badge list */}
                {profile.badges.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                      Badges
                    </h4>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                      {profile.badges.map((badge) => (
                        <div
                          key={badge.id}
                          className={`rounded-lg p-3 text-center border ${
                            badge.earned
                              ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800'
                              : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 opacity-50'
                          }`}
                        >
                          <div className="text-2xl mb-1">{badge.icon}</div>
                          <div
                            className={`text-xs font-medium ${
                              badge.earned
                                ? 'text-gray-900 dark:text-gray-100'
                                : 'text-gray-500 dark:text-gray-500'
                            }`}
                          >
                            {badge.title}
                          </div>
                          {badge.earned && badge.earned_date && (
                            <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                              {formatDate(badge.earned_date)}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </div>

          {/* Footer */}
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
            <Button variant="ghost" onClick={onClose}>
              Close
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string | number;
  highlight?: boolean;
}) {
  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-center">
      <div
        className={`text-lg font-bold ${
          highlight
            ? 'text-amber-600 dark:text-amber-400'
            : 'text-gray-900 dark:text-gray-100'
        }`}
      >
        {value}
      </div>
      <div className="text-xs text-gray-600 dark:text-gray-400">{label}</div>
    </div>
  );
}
