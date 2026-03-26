'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { SignInModal } from '@/components/layout/SignInModal';
import { apiClient } from '@/lib/api';

export interface NavbarProps {
  showProgress?: boolean;
  progressPercentage?: number;
  currentPath?: string;
  isAuthenticated?: boolean;
  userName?: string;
  userAvatar?: string;
  isAdmin?: boolean;
  provider?: string;
  onLogout?: () => void;
}

/**
 * Navbar component with responsive design and optional progress display.
 * Fixed at the top of the viewport with mobile menu support.
 * 
 * @param showProgress - Whether to display the progress bar
 * @param progressPercentage - Progress value (0-100)
 * @param currentPath - Current learning path name to display
 */
export function Navbar({
  showProgress = false,
  progressPercentage = 0,
  currentPath,
  isAuthenticated = false,
  userName = 'User',
  userAvatar,
  isAdmin = false,
  provider,
  onLogout
}: NavbarProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [isSignInModalOpen, setIsSignInModalOpen] = useState(false);
  const pathname = usePathname();

  const handleLogout = () => {
    setIsProfileMenuOpen(false);
    if (onLogout) {
      onLogout();
    } else {
      window.location.href = '/';
    }
  };

  const handleSignIn = () => {
    setIsSignInModalOpen(true);
  };

  // Helper function to determine if a link is active
  const isLinkActive = (path: string) => {
    if (!pathname) return false;
    return pathname.startsWith(path);
  };

  // Helper function to get link classes with active state
  const getLinkClasses = (path: string, baseClasses: string) => {
    const isActive = isLinkActive(path);
    return `${baseClasses} ${isActive ? 'text-primary-500 dark:text-primary-400' : ''}`;
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 h-16">
      <div className="h-full px-6 flex items-center justify-between">
        {/* Logo/Title Section */}
        <div className="flex items-center space-x-4">
          <a 
            href={isAuthenticated ? "/dashboard" : "/"}
            className="flex items-center space-x-3 group transition-all"
            aria-label={isAuthenticated ? "Go to Dashboard" : "Go to Home"}
          >
            {/* Logo Icon */}
            <img 
              src="/light_mode_logo.svg" 
              alt="The DevSec Blueprint Logo" 
              className="h-10 w-auto dark:hidden"
            />
            <img 
              src="/dark_mode_logo.svg" 
              alt="The DevSec Blueprint Logo" 
              className="h-10 w-auto hidden dark:block"
            />
            {/* Title */}
            <div className="text-xl font-bold text-gray-900 dark:text-gray-100 group-hover:text-[#d4a500] dark:group-hover:text-[#ffbe00] transition-colors">
              DSB
            </div>
          </a>
          
          {/* Current Path - Hidden on mobile */}
          {currentPath && (
            <div className="hidden md:flex items-center">
              <span className="text-gray-400 dark:text-gray-600 mx-2">/</span>
              <span className="text-gray-600 dark:text-gray-400 text-sm">{currentPath}</span>
            </div>
          )}
        </div>

        {/* Progress Display - Hidden on mobile */}
        {showProgress && (
          <div className="hidden md:flex items-center space-x-3 flex-1 max-w-xs mx-8">
            <ProgressBar 
              percentage={progressPercentage} 
              height="sm"
            />
            <span className="text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">
              {progressPercentage}%
            </span>
          </div>
        )}

        {/* Right Section */}
        <div className="flex items-center space-x-2 lg:space-x-6">
          {/* Courses Link - Only for authenticated users */}
          {isAuthenticated && (
            <a
              href="/courses"
              className={getLinkClasses(
                '/courses',
                'hidden lg:inline-flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors'
              )}
              aria-current={isLinkActive('/learn') ? 'page' : undefined}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <span>Courses</span>
            </a>
          )}

          {/* Walkthroughs Link - Only for authenticated users */}
          {isAuthenticated && (
            <a
              href="/walkthroughs"
              className={getLinkClasses(
                '/walkthroughs',
                'hidden lg:inline-flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors'
              )}
              aria-current={isLinkActive('/walkthroughs') ? 'page' : undefined}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
              <span>Walkthroughs</span>
            </a>
          )}

          {/* Dashboard Link - Only for authenticated users */}
          {isAuthenticated && (
            <a
              href="/dashboard"
              className={getLinkClasses(
                '/dashboard',
                'hidden lg:inline-flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors'
              )}
              aria-current={isLinkActive('/dashboard') ? 'page' : undefined}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              <span>Dashboard</span>
            </a>
          )}

          {/* Admin Link - Only for admin users */}
          {isAuthenticated && isAdmin && (
            <a
              href="/admin"
              className={getLinkClasses(
                '/admin',
                'hidden lg:inline-flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors'
              )}
              aria-current={isLinkActive('/admin') ? 'page' : undefined}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>Admin</span>
            </a>
          )}

          {/* Curriculum Link - Only for unauthenticated users */}
          {!isAuthenticated && (
            <a
              href="/curriculum"
              className={getLinkClasses(
                '/curriculum',
                'hidden lg:inline-flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors'
              )}
              aria-current={isLinkActive('/curriculum') ? 'page' : undefined}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <span>Curriculum</span>
            </a>
          )}

          {/* FAQ Link - Always visible */}
          <a
            href="/faq"
            className={getLinkClasses(
              '/faq',
              'hidden lg:inline-flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors'
            )}
            aria-current={isLinkActive('/faq') ? 'page' : undefined}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>FAQ</span>
          </a>

          {/* Navigation Links - Hidden on mobile, alphabetically ordered */}
          {!showProgress && (
            <div className="hidden xl:flex items-center space-x-4">
              <a 
                href="https://discord.gg/SkYECC4TD8" 
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors"
                aria-label="Join our Discord"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M20.317 4.37a19.791 19.791 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.736 19.736 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 00-.041-.106 13.107 13.107 0 01-1.872-.892.077.077 0 01-.008-.128 10.2 10.2 0 00.372-.292.074.074 0 01.077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 01.078.01c.12.098.246.198.373.292a.077.077 0 01-.006.127 12.299 12.299 0 01-1.873.892.077.077 0 00-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.839 19.839 0 006.002-3.03.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 00-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
                </svg>
              </a>
              <a 
                href="https://github.com/devsecblueprint/devsecblueprint" 
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors"
                aria-label="Visit our GitHub"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 16 16" aria-hidden="true">
                  <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                </svg>
              </a>
              <a 
                href="https://shop.devsecblueprint.com/" 
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors"
                aria-label="SWAG Shop"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
              </a>
              <a 
                href="https://youtube.com/@damienjburks" 
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors"
                aria-label="Visit our YouTube channel"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                </svg>
              </a>
            </div>
          )}

          {/* Theme Toggle */}
          <ThemeToggle />

          {/* Authenticated User Profile or Sign In Button */}
          {isAuthenticated ? (
            <div className="relative hidden md:block">
              <button
                onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
                className="flex items-center space-x-2 p-2 min-w-[44px] min-h-[44px] rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400"
                aria-label="User menu"
                aria-expanded={isProfileMenuOpen}
              >
                {userAvatar ? (
                  <img 
                    src={userAvatar} 
                    alt={userName}
                    className="w-8 h-8 rounded-full"
                  />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-primary-400 flex items-center justify-center text-gray-900 font-semibold">
                    {userName.charAt(0).toUpperCase()}
                  </div>
                )}
                <svg 
                  className={`w-4 h-4 text-gray-600 dark:text-gray-400 transition-transform ${isProfileMenuOpen ? 'rotate-180' : ''}`}
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Profile Dropdown */}
              {isProfileMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg shadow-lg py-2 z-50">
                  <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800">
                    <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">{userName}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Signed in with {provider === 'gitlab' ? 'GitLab' : 'GitHub'}</p>
                  </div>
                  <a
                    href="/dashboard"
                    className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  >
                    Dashboard
                  </a>
                  {/* Admin Link - Only for admin users */}
                  {isAdmin && (
                    <a
                      href="/admin"
                      className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      <span>Admin Dashboard</span>
                    </a>
                  )}
                  <div className="border-t border-gray-200 dark:border-gray-800 my-2"></div>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  >
                    Sign Out
                  </button>
                  <button
                    onClick={async () => {
                      if (confirm('Are you sure you want to delete your account? This will permanently delete all your progress and data. This action cannot be undone.')) {
                        setIsProfileMenuOpen(false);
                        try {
                          const { error } = await apiClient.deleteAccount();
                          if (error) {
                            alert(`Failed to delete account: ${error}`);
                          } else {
                            alert('Your account has been successfully deleted.');
                            if (onLogout) {
                              onLogout();
                            } else {
                              window.location.href = '/';
                            }
                          }
                        } catch (err) {
                          alert('An error occurred while deleting your account. Please try again.');
                        }
                      }
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  >
                    Delete Account
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button
              onClick={handleSignIn}
              className="hidden md:inline-flex items-center space-x-2 px-4 py-2 min-h-[44px] text-sm font-semibold text-gray-900 bg-primary-400 hover:bg-primary-500 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-900"
            >
              <span>Log in</span>
            </button>
          )}

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="lg:hidden p-3 min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-400 dark:focus:ring-gray-600"
            aria-label="Toggle mobile menu"
            aria-expanded={isMobileMenuOpen}
          >
            {isMobileMenuOpen ? (
              <svg 
                className="w-6 h-6" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M6 18L18 6M6 6l12 12" 
                />
              </svg>
            ) : (
              <svg 
                className="w-6 h-6" 
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
            )}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {isMobileMenuOpen && (
        <div className="lg:hidden bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 px-6 py-4">
          {/* Dashboard Link on Mobile - Only for authenticated users */}
          {isAuthenticated && (
            <div className="mb-4 pb-4 border-b border-gray-200 dark:border-gray-800">
              <a
                href="/dashboard"
                className={getLinkClasses(
                  '/dashboard',
                  'flex items-center space-x-2 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors'
                )}
                aria-current={isLinkActive('/dashboard') ? 'page' : undefined}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
                <span>Dashboard</span>
              </a>
              <a
                href="/courses"
                className={getLinkClasses(
                  '/courses',
                  'flex items-center space-x-2 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors'
                )}
                aria-current={isLinkActive('/courses') ? 'page' : undefined}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <span>Courses</span>
              </a>
              <a
                href="/walkthroughs"
                className={getLinkClasses(
                  '/walkthroughs',
                  'flex items-center space-x-2 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors'
                )}
                aria-current={isLinkActive('/walkthroughs') ? 'page' : undefined}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
                <span>Walkthroughs</span>
              </a>
              <a
                href="/faq"
                className={getLinkClasses(
                  '/faq',
                  'flex items-center space-x-2 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors'
                )}
                aria-current={isLinkActive('/faq') ? 'page' : undefined}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>FAQ</span>
              </a>
            </div>
          )}

          {/* Navigation Links on Mobile - Alphabetically ordered */}
          <div className="space-y-3 mb-4">
            {/* Curriculum Link - Only for unauthenticated users on mobile */}
            {!isAuthenticated && (
              <a 
                href="/curriculum"
                className={getLinkClasses(
                  '/curriculum',
                  'flex items-center space-x-2 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors'
                )}
                aria-current={isLinkActive('/curriculum') ? 'page' : undefined}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <span>Curriculum</span>
              </a>
            )}
            {/* FAQ Link - Always visible on mobile */}
            {!isAuthenticated && (
              <a 
                href="/faq"
                className={getLinkClasses(
                  '/faq',
                  'flex items-center space-x-2 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors'
                )}
                aria-current={isLinkActive('/faq') ? 'page' : undefined}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>FAQ</span>
              </a>
            )}
            <a 
              href="https://discord.gg/SkYECC4TD8" 
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M20.317 4.37a19.791 19.791 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.736 19.736 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 00-.041-.106 13.107 13.107 0 01-1.872-.892.077.077 0 01-.008-.128 10.2 10.2 0 00.372-.292.074.074 0 01.077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 01.078.01c.12.098.246.198.373.292a.077.077 0 01-.006.127 12.299 12.299 0 01-1.873.892.077.077 0 00-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.839 19.839 0 006.002-3.03.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 00-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
              </svg>
              <span>Discord</span>
            </a>
            <a 
              href="https://github.com/devsecblueprint/devsecblueprint" 
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 16 16" aria-hidden="true">
                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
              </svg>
              <span>GitHub</span>
            </a>
            <a 
              href="https://shop.devsecblueprint.com/" 
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
              <span>SWAG Shop</span>
            </a>
            <a 
              href="https://youtube.com/@damienjburks" 
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400 transition-colors"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
              </svg>
              <span>YouTube</span>
            </a>
          </div>

          {/* Sign In Button or Profile on Mobile */}
          <div className="md:hidden mb-4 pb-4 border-b border-gray-200 dark:border-gray-800">
            {isAuthenticated ? (
              <div>
                <div className="flex items-center space-x-3 mb-4">
                  {userAvatar ? (
                    <img 
                      src={userAvatar} 
                      alt={userName}
                      className="w-12 h-12 rounded-full"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-full bg-primary-400 flex items-center justify-center text-gray-900 font-bold text-lg">
                      {userName.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div>
                    <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">{userName}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-500">Signed in with {provider === 'gitlab' ? 'GitLab' : 'GitHub'}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <a
                    href="/dashboard"
                    className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                  >
                    Dashboard
                  </a>
                  {/* Admin Link - Only for admin users on mobile */}
                  {isAdmin && (
                    <a
                      href="/admin"
                      className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      <span>Admin Dashboard</span>
                    </a>
                  )}
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                  >
                    Sign Out
                  </button>
                  <button
                    onClick={async () => {
                      if (confirm('Are you sure you want to delete your account? This will permanently delete all your progress and data. This action cannot be undone.')) {
                        setIsMobileMenuOpen(false);
                        try {
                          const { error } = await apiClient.deleteAccount();
                          if (error) {
                            alert(`Failed to delete account: ${error}`);
                          } else {
                            alert('Your account has been successfully deleted.');
                            if (onLogout) {
                              onLogout();
                            } else {
                              window.location.href = '/';
                            }
                          }
                        } catch (err) {
                          alert('An error occurred while deleting your account. Please try again.');
                        }
                      }
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                  >
                    Delete Account
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={handleSignIn}
                className="flex items-center justify-center space-x-2 w-full px-4 py-3 text-sm font-semibold text-gray-900 bg-primary-400 hover:bg-primary-500 rounded-lg transition-colors"
              >
                <span>Log in</span>
              </button>
            )}
          </div>

          {/* Current Path on Mobile */}
          {currentPath && (
            <div className="mb-4">
              <span className="text-xs text-gray-500 dark:text-gray-500 uppercase tracking-wide">Current Path</span>
              <div className="text-gray-700 dark:text-gray-300 mt-1">{currentPath}</div>
            </div>
          )}

          {/* Progress on Mobile */}
          {showProgress && (
            <div className="mb-4">
              <span className="text-xs text-gray-500 dark:text-gray-500 uppercase tracking-wide">Progress</span>
              <div className="mt-2">
                <ProgressBar 
                  percentage={progressPercentage} 
                  height="sm"
                  showLabel
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Sign In Modal */}
      <SignInModal isOpen={isSignInModalOpen} onClose={() => setIsSignInModalOpen(false)} />
    </nav>
  );
}
