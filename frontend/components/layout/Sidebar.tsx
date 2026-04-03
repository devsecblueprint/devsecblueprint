'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { Module, Page } from '@/lib/types';

const SIDEBAR_NAV_STATE_KEY = 'sidebar-nav-state';

export interface SidebarNavState {
  [moduleId: string]: boolean; // true = expanded, false = collapsed
}

/**
 * Compute default expand/collapse state when no persisted state exists.
 * - Completed modules → collapsed
 * - Module containing current page → expanded
 * - All other modules → collapsed
 */
export function computeDefaultNavState(
  modules: Module[],
  currentPageId?: string
): SidebarNavState {
  const state: SidebarNavState = {};
  for (const mod of modules) {
    const allCompleted = mod.pages.length > 0 && mod.pages.every(p => p.completed);
    const containsCurrentPage = mod.pages.some(p => p.id === currentPageId);
    // Current page's module is expanded even if completed
    state[mod.id] = containsCurrentPage ? true : !allCompleted ? false : false;
  }
  return state;
}

/**
 * Read sidebar nav state from localStorage. Returns null if not found or on error.
 */
export function readNavState(): SidebarNavState | null {
  try {
    const raw = localStorage.getItem(SIDEBAR_NAV_STATE_KEY);
    if (raw === null) return null;
    const parsed = JSON.parse(raw);
    if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
      // Corrupted — clear and return null
      localStorage.removeItem(SIDEBAR_NAV_STATE_KEY);
      return null;
    }
    return parsed as SidebarNavState;
  } catch {
    // JSON parse error or localStorage error — clear and fall back
    try {
      localStorage.removeItem(SIDEBAR_NAV_STATE_KEY);
    } catch {
      // Ignore removal errors (e.g., private browsing)
    }
    return null;
  }
}

/**
 * Write sidebar nav state to localStorage. Silently fails on error.
 */
export function writeNavState(state: SidebarNavState): void {
  try {
    localStorage.setItem(SIDEBAR_NAV_STATE_KEY, JSON.stringify(state));
  } catch {
    // Silently fail (private browsing, quota exceeded)
  }
}

/**
 * Apply auto-expand for the module containing the current page,
 * preserving all other modules' states.
 */
export function applyAutoExpand(
  state: SidebarNavState,
  modules: Module[],
  currentPageId?: string
): SidebarNavState {
  if (!currentPageId) return state;
  const moduleWithCurrentPage = modules.find(m =>
    m.pages.some(p => p.id === currentPageId)
  );
  if (!moduleWithCurrentPage) return state;
  if (state[moduleWithCurrentPage.id] === true) return state;
  return { ...state, [moduleWithCurrentPage.id]: true };
}

export interface SidebarProps {
  modules: Module[];
  currentPageId?: string;
}

export function Sidebar({ modules, currentPageId }: SidebarProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('sidebar-collapsed') === 'true';
    }
    return false;
  });
  const [expandedModules, setExpandedModules] = useState<Set<string>>(() => {
    if (typeof window === 'undefined') {
      return new Set(modules.map(m => m.id));
    }
    // Read persisted state or compute defaults
    let navState = readNavState();
    if (!navState) {
      navState = computeDefaultNavState(modules, currentPageId);
    }
    // Auto-expand the module containing the current page
    navState = applyAutoExpand(navState, modules, currentPageId);
    // Persist the resolved state
    writeNavState(navState);
    // Convert to Set
    return new Set(
      Object.entries(navState)
        .filter(([, expanded]) => expanded)
        .map(([id]) => id)
    );
  });
  const currentPageRef = useRef<HTMLAnchorElement>(null);
  const sidebarRef = useRef<HTMLDivElement>(null);
  const scrollPositionKey = 'sidebar-scroll-position';

  // Save collapsed state to localStorage and update CSS variable
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('sidebar-collapsed', String(isCollapsed));
      document.documentElement.style.setProperty(
        '--sidebar-width',
        isCollapsed ? '3.5rem' : '17.5rem'
      );
    }
  }, [isCollapsed]);

  // Save scroll position whenever user scrolls
  useEffect(() => {
    const sidebar = sidebarRef.current;
    if (!sidebar) return;

    const saveScrollPosition = () => {
      sessionStorage.setItem(scrollPositionKey, String(sidebar.scrollTop));
    };

    // Save on scroll
    sidebar.addEventListener('scroll', saveScrollPosition, { passive: true });
    
    // Save before navigation
    const handleBeforeUnload = () => {
      saveScrollPosition();
    };
    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      sidebar.removeEventListener('scroll', saveScrollPosition);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  // Ensure the module containing the current page is expanded and persist
  useEffect(() => {
    const moduleWithCurrentPage = modules.find(module =>
      module.pages.some(page => page.id === currentPageId)
    );
    
    if (moduleWithCurrentPage) {
      setExpandedModules(prev => {
        if (prev.has(moduleWithCurrentPage.id)) return prev;
        const newSet = new Set(prev);
        newSet.add(moduleWithCurrentPage.id);
        // Persist updated state
        const navState: SidebarNavState = {};
        for (const mod of modules) {
          navState[mod.id] = newSet.has(mod.id);
        }
        writeNavState(navState);
        return newSet;
      });
    }
  }, [currentPageId, modules]);

  // Scroll to current page when page changes
  useEffect(() => {
    const sidebar = sidebarRef.current;
    const currentPage = currentPageRef.current;
    if (!sidebar || !currentPage) return;

    // Use a delay to ensure the DOM is fully rendered after page reload
    const timeoutId = setTimeout(() => {
      currentPage.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      });
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [currentPageId]);

  // Filter out walkthroughs and group modules by learning path
  const groupedModules = modules
    .filter(module => {
      const learningPath = (module as any).learningPath || 'Other';
      return learningPath !== 'Walkthroughs';
    })
    .reduce((acc, module) => {
      const learningPath = (module as any).learningPath || 'Other';
      if (!acc[learningPath]) {
        acc[learningPath] = [];
      }
      acc[learningPath].push(module);
      return acc;
    }, {} as { [key: string]: Module[] });

  const toggleModule = (moduleId: string) => {
    setExpandedModules(prev => {
      const newSet = new Set(prev);
      if (newSet.has(moduleId)) {
        newSet.delete(moduleId);
      } else {
        newSet.add(moduleId);
      }
      // Persist updated state to localStorage
      const navState: SidebarNavState = {};
      for (const mod of modules) {
        navState[mod.id] = newSet.has(mod.id);
      }
      writeNavState(navState);
      return newSet;
    });
  };

  const sidebarContent = (
    <aside ref={sidebarRef} className="h-full bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 overflow-y-auto overscroll-contain">
      <div className={`transition-all ${isCollapsed ? 'p-2' : 'p-6'}`}>
        <div className={`flex items-center mb-4 ${isCollapsed ? 'justify-center' : 'justify-between'}`}>
          {!isCollapsed && (
            <h2 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide whitespace-nowrap overflow-hidden">
              Course Content
            </h2>
          )}
          {/* Desktop Collapse Button */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="hidden md:flex items-center justify-center w-10 h-10 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 flex-shrink-0"
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <svg
              className={`w-5 h-5 text-gray-600 dark:text-gray-400 transition-transform ${
                isCollapsed ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
              />
            </svg>
          </button>
        </div>
        
        {!isCollapsed && (
          <nav aria-label="Course modules">
            {Object.entries(groupedModules).map(([learningPath, pathModules]) => (
            <div key={learningPath} className="mb-6">
              {/* Learning Path Header */}
              <h3 className="text-xs font-bold text-primary-500 dark:text-primary-400 uppercase tracking-wider mb-3 px-3">
                {learningPath}
              </h3>
              
              <ul className="space-y-2">
                {pathModules.map((module) => {
              const isExpanded = expandedModules.has(module.id);
              const completedPages = module.pages.filter(p => p.completed).length;
              const totalPages = module.pages.length;
              const allCompleted = completedPages === totalPages;

              return (
                <li key={module.id}>
                  {/* Module Header */}
                  <button
                    onClick={() => toggleModule(module.id)}
                    className="w-full flex items-center gap-2 p-3 min-h-[44px] rounded-lg text-left hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400"
                    aria-expanded={isExpanded}
                    aria-controls={`module-${module.id}-pages`}
                  >
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
                        <div className="w-5 h-5 rounded-full border-2 border-gray-400 dark:border-gray-600" aria-hidden="true" />
                      )}
                    </div>

                    {/* Module Title */}
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100 flex-1 min-w-0 truncate">
                      {module.title}
                    </span>

                    {/* Progress and Expand Icon */}
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className="text-xs text-gray-500 dark:text-gray-500 whitespace-nowrap">
                        {completedPages}/{totalPages}
                      </span>
                      <svg
                        className={`w-4 h-4 text-gray-600 dark:text-gray-400 transition-transform ${
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
                            <Link
                              ref={isCurrentPage ? currentPageRef : null}
                              href={page.slug}
                              className={`flex items-center space-x-3 p-3 min-h-[44px] rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 ${
                                isCurrentPage
                                  ? 'bg-gray-100 dark:bg-gray-800 text-primary-500 dark:text-primary-400'
                                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-200'
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
                                    className="w-4 h-4 rounded-full border-2 border-gray-400 dark:border-gray-600"
                                    aria-label="Not completed"
                                  />
                                )}
                              </div>

                              {/* Page Title */}
                              <span className="text-sm truncate">{page.title}</span>
                            </Link>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </li>
              );
            })}
          </ul>
            </div>
          ))}
          </nav>
        )}
      </div>
    </aside>
  );

  return (
    <>
      {/* Mobile Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="md:hidden fixed bottom-20 right-4 z-50 w-12 h-12 min-w-[48px] min-h-[48px] bg-primary-400 text-gray-900 rounded-full shadow-lg hover:bg-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 focus:ring-offset-gray-950 flex items-center justify-center"
        aria-label="Toggle sidebar"
        aria-expanded={isOpen}
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
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
      </button>

      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-gray-950 bg-opacity-75"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Desktop Sidebar */}
      <div className={`hidden md:block fixed left-0 top-16 h-[calc(100vh-4rem)] transition-all duration-300 ${isCollapsed ? 'w-14' : 'w-70'}`}>
        {sidebarContent}
      </div>

      {/* Mobile Sidebar */}
      <div
        className={`md:hidden fixed left-0 top-16 h-[calc(100vh-4rem)] w-full max-w-[320px] z-40 transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {sidebarContent}
      </div>
    </>
  );
}
