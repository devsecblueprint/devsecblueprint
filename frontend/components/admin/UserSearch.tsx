'use client';

import { useState } from 'react';
import { apiClient } from '@/lib/api';
import { CenteredSpinner } from '@/components/ui/Spinner';

export function UserSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    setIsSearching(true);
    setError(null);
    setHasSearched(true);

    try {
      const { data, error: apiError } = await apiClient.searchUsers(query.trim());
      
      if (apiError) {
        setError(apiError);
        setResults([]);
      } else if (data) {
        setResults(data.users);
      }
    } catch (err) {
      setError('Failed to search users');
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
        User Search
      </h2>

      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex space-x-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by username..."
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400"
          />
          <button
            type="submit"
            disabled={isSearching}
            className="px-6 py-2 bg-amber-500 hover:bg-amber-600 dark:bg-amber-600 dark:hover:bg-amber-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSearching ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {error && (
        <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {isSearching ? (
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 py-16">
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="w-12 h-12 border-4 border-gray-200 dark:border-gray-700 border-t-amber-500 dark:border-t-amber-400 rounded-full animate-spin" />
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Searching for users...
            </p>
          </div>
        </div>
      ) : hasSearched ? (
        results.length > 0 ? (
          <div className="space-y-3">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
              Found {results.length} user{results.length !== 1 ? 's' : ''}
            </p>
            {results.map((user) => (
              <div
                key={user.user_id}
                className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    {user.avatar_url && (
                      <img
                        src={user.avatar_url}
                        alt={user.username}
                        className="w-12 h-12 rounded-full"
                      />
                    )}
                    <div>
                      <div className="font-semibold text-gray-900 dark:text-gray-100">
                        {user.username}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        @{user.gitlab_username || user.github_username}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                        Registered: {new Date(user.registered_at).toLocaleDateString()}
                      </div>
                      {user.last_login && (
                        <div className="text-xs text-gray-500 dark:text-gray-500">
                          Last Active: {new Date(user.last_login).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                      {user.stats.overall_completion}%
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-500">
                      Completion
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-5 gap-4 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div>
                    <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {user.stats.completed_count}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      Lessons
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {user.stats.walkthroughs_completed}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      Walkthroughs
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {user.stats.quizzes_passed}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      Quizzes
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {user.stats.badges_earned}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      Badges
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {user.stats.capstone_submissions}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      Capstones
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-600 dark:text-gray-400">
            No users found matching "{query}"
          </div>
        )
      ) : (
        <div className="text-center py-12 text-gray-500 dark:text-gray-500">
          Enter a username to search
        </div>
      )}
    </div>
  );
}
