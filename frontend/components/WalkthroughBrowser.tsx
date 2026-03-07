'use client';

import { useEffect, useState, useMemo, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { WalkthroughWithProgress } from '@/lib/types';
import { Button } from '@/components/ui/Button';

interface WalkthroughBrowserProps {
  initialWalkthroughs: WalkthroughWithProgress[];
}

const ITEMS_PER_PAGE = 12; // Display 12 walkthroughs per page (4x3 grid)

export function WalkthroughBrowser({ initialWalkthroughs }: WalkthroughBrowserProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const mainHeadingRef = useRef<HTMLHeadingElement>(null);
  
  // State for filters
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');
  const [difficultyFilter, setDifficultyFilter] = useState<string>(searchParams.get('difficulty') || 'All');
  const [statusFilter, setStatusFilter] = useState<string>(searchParams.get('status') || 'All');
  const [currentPage, setCurrentPage] = useState(1);

  // Focus management: focus on main heading when component mounts
  useEffect(() => {
    if (mainHeadingRef.current) {
      mainHeadingRef.current.focus();
    }
  }, []);

  // Filter walkthroughs based on current filters
  const filteredWalkthroughs = useMemo(() => {
    return initialWalkthroughs.filter(walkthrough => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesSearch = 
          walkthrough.title.toLowerCase().includes(query) ||
          walkthrough.description.toLowerCase().includes(query) ||
          walkthrough.topics.some(topic => topic.toLowerCase().includes(query));
        
        if (!matchesSearch) return false;
      }

      // Difficulty filter
      if (difficultyFilter !== 'All' && walkthrough.difficulty !== difficultyFilter) {
        return false;
      }

      // Status filter
      if (statusFilter !== 'All') {
        if (statusFilter === 'in_progress' && walkthrough.progress.status !== 'in_progress') {
          return false;
        }
        if (statusFilter === 'completed' && walkthrough.progress.status !== 'completed') {
          return false;
        }
      }

      return true;
    });
  }, [initialWalkthroughs, searchQuery, difficultyFilter, statusFilter]);

  // Calculate pagination
  const totalPages = Math.ceil(filteredWalkthroughs.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const paginatedWalkthroughs = filteredWalkthroughs.slice(startIndex, endIndex);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, difficultyFilter, statusFilter]);

  // Sync filters with URL query parameters
  useEffect(() => {
    const params = new URLSearchParams();
    
    if (searchQuery) params.set('search', searchQuery);
    if (difficultyFilter !== 'All') params.set('difficulty', difficultyFilter);
    if (statusFilter !== 'All') params.set('status', statusFilter);
    
    const queryString = params.toString();
    const newUrl = queryString ? `/walkthroughs?${queryString}` : '/walkthroughs';
    
    router.replace(newUrl, { scroll: false });
  }, [searchQuery, difficultyFilter, statusFilter, router]);

  // Clear all filters
  const clearFilters = () => {
    setSearchQuery('');
    setDifficultyFilter('All');
    setStatusFilter('All');
  };

  // Check if any filters are active
  const hasActiveFilters = searchQuery || difficultyFilter !== 'All' || statusFilter !== 'All';

  // Get difficulty badge color
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Beginner':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'Intermediate':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'Advanced':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  // Get status badge color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  // Format status text
  const formatStatus = (status: string) => {
    switch (status) {
      case 'not_started':
        return 'Not Started';
      case 'in_progress':
        return 'In Progress';
      case 'completed':
        return 'Completed';
      default:
        return status;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="mb-8">
        <h1 
          ref={mainHeadingRef}
          tabIndex={-1}
          className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2 focus:outline-none"
        >
          Walkthroughs
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Explore hands-on labs and reference implementations
        </p>
      </div>

      {/* Filters Section */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6 space-y-4">
        {/* Search Input */}
        <div>
          <label htmlFor="search" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Search
          </label>
          <input
            id="search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by title, description, or topics..."
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            aria-label="Search walkthroughs"
          />
        </div>

        {/* Difficulty Filter */}
        <div>
          <label htmlFor="difficulty" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Difficulty
          </label>
          <select
            id="difficulty"
            value={difficultyFilter}
            onChange={(e) => setDifficultyFilter(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            aria-label="Filter by difficulty"
          >
            <option value="All">All Levels</option>
            <option value="Beginner">Beginner</option>
            <option value="Intermediate">Intermediate</option>
            <option value="Advanced">Advanced</option>
          </select>
        </div>

        {/* Progress Status Filter */}
        <div>
          <label htmlFor="status" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Progress Status
          </label>
          <select
            id="status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            aria-label="Filter by progress status"
          >
            <option value="All">All Status</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
          </select>
        </div>

        {/* Clear Filters Button */}
        {hasActiveFilters && (
          <div className="pt-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={clearFilters}
              aria-label="Clear all filters"
            >
              Clear Filters
            </Button>
          </div>
        )}
      </div>

      {/* Results Count - ARIA live region for screen reader announcements */}
      <div 
        className="text-sm text-gray-600 dark:text-gray-400"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        Showing {startIndex + 1}-{Math.min(endIndex, filteredWalkthroughs.length)} of {filteredWalkthroughs.length} walkthroughs
      </div>

      {/* Walkthroughs Grid */}
      {filteredWalkthroughs.length === 0 ? (
        <div 
          className="text-center py-12"
          role="status"
          aria-live="polite"
        >
          <p className="text-gray-600 dark:text-gray-400">
            No walkthroughs match your filters. Try adjusting your search criteria.
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {paginatedWalkthroughs.map(walkthrough => (
            <a
              key={walkthrough.id}
              href={`/walkthroughs/${walkthrough.id}`}
              className="block group"
            >
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6 hover:border-primary-400 dark:hover:border-primary-400 transition-all hover:shadow-lg h-full flex flex-col">
                {/* Header with Title and Status */}
                <div className="flex items-start justify-between mb-3">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 group-hover:text-primary-500 dark:group-hover:text-primary-400 transition-colors flex-1">
                    {walkthrough.title}
                  </h2>
                  {walkthrough.progress.status !== 'not_started' && (
                    <span className={`ml-2 px-2 py-1 text-xs font-medium rounded ${getStatusColor(walkthrough.progress.status)}`}>
                      {formatStatus(walkthrough.progress.status)}
                    </span>
                  )}
                </div>

                {/* Description */}
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 flex-1">
                  {walkthrough.description}
                </p>

                {/* Metadata */}
                <div className="space-y-3">
                  {/* Difficulty and Time */}
                  <div className="flex items-center gap-3 text-sm">
                    <span className={`px-2 py-1 rounded font-medium ${getDifficultyColor(walkthrough.difficulty)}`}>
                      {walkthrough.difficulty}
                    </span>
                    <span className="text-gray-600 dark:text-gray-400">
                      {walkthrough.estimatedTime} min
                    </span>
                  </div>

                  {/* Topics */}
                  {walkthrough.topics.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {walkthrough.topics.slice(0, 3).map(topic => (
                        <span
                          key={topic}
                          className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded"
                        >
                          {topic}
                        </span>
                      ))}
                      {walkthrough.topics.length > 3 && (
                        <span className="px-2 py-1 text-xs text-gray-500 dark:text-gray-400">
                          +{walkthrough.topics.length - 3} more
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Action Indicator */}
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-800">
                  <div className="flex items-center text-primary-500 dark:text-primary-400 font-medium text-sm group-hover:text-primary-600 dark:group-hover:text-primary-300 transition-colors">
                    <span>View Walkthrough</span>
                    <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </div>
            </a>
          ))}
        </div>

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-8">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              aria-label="Previous page"
            >
              <svg 
                className="w-5 h-5" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M15 19l-7-7 7-7" 
                />
              </svg>
            </Button>

            <div className="flex items-center gap-2">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => {
                // Show first page, last page, current page, and pages around current
                const showPage = 
                  page === 1 || 
                  page === totalPages || 
                  Math.abs(page - currentPage) <= 1;
                
                // Show ellipsis for gaps
                const showEllipsisBefore = page === currentPage - 2 && currentPage > 3;
                const showEllipsisAfter = page === currentPage + 2 && currentPage < totalPages - 2;

                if (!showPage && !showEllipsisBefore && !showEllipsisAfter) {
                  return null;
                }

                if (showEllipsisBefore || showEllipsisAfter) {
                  return (
                    <span 
                      key={`ellipsis-${page}`}
                      className="px-2 text-gray-500 dark:text-gray-400"
                    >
                      ...
                    </span>
                  );
                }

                return (
                  <button
                    key={page}
                    onClick={() => setCurrentPage(page)}
                    className={`
                      min-w-[2.5rem] px-3 py-2 rounded-lg font-medium transition-colors
                      ${page === currentPage
                        ? 'bg-primary-500 text-white'
                        : 'bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'
                      }
                    `}
                    aria-label={`Go to page ${page}`}
                    aria-current={page === currentPage ? 'page' : undefined}
                  >
                    {page}
                  </button>
                );
              })}
            </div>

            <Button
              variant="secondary"
              size="sm"
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              aria-label="Next page"
            >
              <svg 
                className="w-5 h-5" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M9 5l7 7-7 7" 
                />
              </svg>
            </Button>
          </div>
        )}
      </>
      )}
    </div>
  );
}
