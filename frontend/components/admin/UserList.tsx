'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { apiClient, UserListItem } from '@/lib/api';
import { Spinner } from '@/components/ui/Spinner';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { UserProfileModal } from '@/components/admin/UserProfileModal';
import { format } from 'date-fns';

const PAGE_SIZE = 20;
const DEBOUNCE_MS = 300;

export function UserList() {
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState('');
  const [activeSearch, setActiveSearch] = useState('');
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Fetch users whenever page or activeSearch changes
  useEffect(() => {
    fetchUsers(page, activeSearch);
  }, [page, activeSearch]);

  // Debounce search input → activeSearch
  const handleSearchChange = useCallback((value: string) => {
    setSearchInput(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setPage(1);
      setActiveSearch(value.trim());
    }, DEBOUNCE_MS);
  }, []);

  // Cleanup debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  const fetchUsers = async (p: number, search: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const { data, error: apiError } = await apiClient.listUsers(
        p,
        PAGE_SIZE,
        search || undefined
      );
      if (apiError) {
        setError(apiError);
        return;
      }
      if (data) {
        setUsers(data.users);
        setTotalPages(data.total_pages);
        setTotalCount(data.total_count);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch users');
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

  const providerLabel = (provider: string) =>
    provider === 'gitlab' ? 'GitLab' : provider === 'bitbucket' ? 'Bitbucket Cloud' : 'GitHub';

  const providerUsername = (user: UserListItem) =>
    user.provider === 'gitlab' ? user.gitlab_username : user.provider === 'bitbucket' ? user.bitbucket_username : user.github_username;

  const handlePrev = () => {
    if (page > 1) setPage(page - 1);
  };

  const handleNext = () => {
    if (page < totalPages) setPage(page + 1);
  };

  // Loading state (only show full spinner on initial load, not on search/page changes)
  if (isLoading && users.length === 0 && !activeSearch) {
    return (
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Users
          </h2>
        </div>
        <div className="flex items-center justify-center py-12">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Users
          </h2>
        </div>
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
              <h3 className="text-sm font-semibold text-red-900 dark:text-red-100 mb-1">
                Failed to Load Users
              </h3>
              <p className="text-sm text-red-800 dark:text-red-200 mb-3">{error}</p>
              <button
                onClick={() => fetchUsers(page, activeSearch)}
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

  // Data state (includes empty + populated)
  return (
    <div>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
        <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100">
          Users
        </h2>
        <Badge variant="default" size="sm">
          {totalCount}
        </Badge>
      </div>

      {/* Search bar */}
      <div className="mb-4 relative">
        <input
          type="text"
          value={searchInput}
          onChange={(e) => handleSearchChange(e.target.value)}
          placeholder="Search all users by name..."
          aria-label="Search users"
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400"
        />
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <Spinner size="sm" />
          </div>
        )}
      </div>

      {/* Empty state */}
      {users.length === 0 && !isLoading && (
        <div className="text-center py-12">
          {activeSearch ? (
            <p className="text-gray-600 dark:text-gray-400">
              No users matching &ldquo;{activeSearch}&rdquo;
            </p>
          ) : (
            <>
              <svg
                className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600 mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              <p className="text-gray-600 dark:text-gray-400">No users found</p>
            </>
          )}
        </div>
      )}

      {/* Desktop table view */}
      {users.length > 0 && (
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-800">
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Avatar
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Name
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Username
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Provider
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Registered
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Last Login
                </th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr
                  key={user.user_id}
                  onClick={() => setSelectedUserId(user.user_id)}
                  className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer"
                  role="button"
                  tabIndex={0}
                  aria-label={`View profile for ${user.username}`}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      setSelectedUserId(user.user_id);
                    }
                  }}
                >
                  <td className="py-3 px-4">
                    {user.avatar_url ? (
                      <img
                        src={user.avatar_url}
                        alt={`${user.username}'s avatar`}
                        className="w-8 h-8 rounded-full"
                      />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                        <span className="text-sm font-medium text-amber-600 dark:text-amber-400">
                          {(user.username || '?').charAt(0).toUpperCase()}
                        </span>
                      </div>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {user.username}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      @{providerUsername(user) || 'unknown'}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        user.provider === 'gitlab'
                          ? 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400'
                          : user.provider === 'bitbucket'
                          ? 'bg-[#0052CC]/10 text-[#0052CC] dark:bg-[#0052CC]/20 dark:text-[#4C9AFF]'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
                      }`}
                    >
                      {providerLabel(user.provider)}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {formatDate(user.registered_at)}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {formatDate(user.last_login)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Mobile card view */}
      {users.length > 0 && (
        <div className="md:hidden space-y-3">
          {users.map((user) => (
            <div
              key={user.user_id}
              onClick={() => setSelectedUserId(user.user_id)}
              className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 cursor-pointer hover:ring-2 hover:ring-amber-500/50 transition-all"
              role="button"
              tabIndex={0}
              aria-label={`View profile for ${user.username}`}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  setSelectedUserId(user.user_id);
                }
              }}
            >
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  {user.avatar_url ? (
                    <img
                      src={user.avatar_url}
                      alt={`${user.username}'s avatar`}
                      className="w-10 h-10 rounded-full"
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                      <span className="text-base font-medium text-amber-600 dark:text-amber-400">
                        {(user.username || '?').charAt(0).toUpperCase()}
                      </span>
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                    {user.username}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-500">
                    @{providerUsername(user) || 'unknown'} ·{' '}
                    <span
                      className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium ${
                        user.provider === 'gitlab'
                          ? 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400'
                          : user.provider === 'bitbucket'
                          ? 'bg-[#0052CC]/10 text-[#0052CC] dark:bg-[#0052CC]/20 dark:text-[#4C9AFF]'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
                      }`}
                    >
                      {providerLabel(user.provider)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination controls */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <Button
          variant="ghost"
          size="sm"
          onClick={handlePrev}
          disabled={page <= 1}
        >
          Previous
        </Button>
        <span className="text-sm text-gray-600 dark:text-gray-400">
          Page {page} of {totalPages} · {totalCount} users
        </span>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleNext}
          disabled={page >= totalPages}
        >
          Next
        </Button>
      </div>

      {/* User Profile Modal */}
      {selectedUserId && (
        <UserProfileModal
          userId={selectedUserId}
          onClose={() => setSelectedUserId(null)}
        />
      )}
    </div>
  );
}
