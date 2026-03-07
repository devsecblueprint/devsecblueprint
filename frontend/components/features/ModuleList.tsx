'use client';

import { useState } from 'react';
import { Module } from '@/lib/types';

export interface ModuleListProps {
  modules: Module[];
  currentPageId?: string;
  onPageClick?: (pageId: string) => void;
}

export function ModuleList({ modules, currentPageId, onPageClick }: ModuleListProps) {
  const [expandedModules, setExpandedModules] = useState<Set<string>>(
    new Set(modules.map(m => m.id))
  );

  const toggleModule = (moduleId: string) => {
    setExpandedModules(prev => {
      const newSet = new Set(prev);
      if (newSet.has(moduleId)) {
        newSet.delete(moduleId);
      } else {
        newSet.add(moduleId);
      }
      return newSet;
    });
  };

  const handlePageClick = (pageId: string, event: React.MouseEvent) => {
    if (onPageClick) {
      event.preventDefault();
      onPageClick(pageId);
    }
  };

  return (
    <nav aria-label="Course modules">
      <ul className="space-y-2">
        {modules.map((module) => {
          const isExpanded = expandedModules.has(module.id);
          const completedPages = module.pages.filter(p => p.completed).length;
          const totalPages = module.pages.length;
          const allCompleted = completedPages === totalPages;

          return (
            <li key={module.id}>
              {/* Module Header */}
              <button
                onClick={() => toggleModule(module.id)}
                className="w-full flex items-center justify-between p-3 rounded-lg text-left hover:bg-gray-800 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400"
                aria-expanded={isExpanded}
                aria-controls={`module-${module.id}-pages`}
              >
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  {/* Completion Icon */}
                  <div className="flex-shrink-0">
                    {allCompleted ? (
                      <svg
                        className="w-5 h-5 text-primary-400"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                        aria-hidden="true"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      <div className="w-5 h-5 rounded-full border-2 border-gray-600" aria-hidden="true" />
                    )}
                  </div>

                  {/* Module Title */}
                  <span className="text-sm font-medium text-gray-100 truncate">
                    {module.title}
                  </span>
                </div>

                {/* Progress and Expand Icon */}
                <div className="flex items-center space-x-2 flex-shrink-0 ml-2">
                  <span className="text-xs text-gray-500">
                    {completedPages}/{totalPages}
                  </span>
                  <svg
                    className={`w-4 h-4 text-gray-400 transition-transform ${
                      isExpanded ? 'transform rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </div>
              </button>

              {/* Pages List */}
              {isExpanded && (
                <ul
                  id={`module-${module.id}-pages`}
                  className="mt-2 ml-8 space-y-1"
                >
                  {module.pages.map((page) => {
                    const isCurrentPage = page.id === currentPageId;

                    return (
                      <li key={page.id}>
                        <a
                          href={`#${page.slug}`}
                          onClick={(e) => handlePageClick(page.id, e)}
                          className={`flex items-center space-x-3 p-2 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 ${
                            isCurrentPage
                              ? 'bg-gray-800 text-primary-400'
                              : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                          }`}
                          aria-current={isCurrentPage ? 'page' : undefined}
                        >
                          {/* Completion Check Icon */}
                          <div className="flex-shrink-0">
                            {page.completed ? (
                              <svg
                                className="w-4 h-4 text-primary-400"
                                fill="currentColor"
                                viewBox="0 0 20 20"
                                aria-label="Completed"
                              >
                                <path
                                  fillRule="evenodd"
                                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                  clipRule="evenodd"
                                />
                              </svg>
                            ) : (
                              <div
                                className="w-4 h-4 rounded-full border-2 border-gray-600"
                                aria-label="Not completed"
                              />
                            )}
                          </div>

                          {/* Page Title */}
                          <span className="text-sm truncate">{page.title}</span>
                        </a>
                      </li>
                    );
                  })}
                </ul>
              )}
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
