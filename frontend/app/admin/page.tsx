'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { useAuth } from '@/lib/hooks/useAuth';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { AuthGuard } from '@/components/AuthGuard';
import { apiClient } from '@/lib/api';
import { CapstoneSubmissions } from '@/components/admin/CapstoneSubmissions';
import { UserList } from '@/components/admin/UserList';
import { WalkthroughStatistics } from '@/components/admin/WalkthroughStatistics';
import { ActiveSessionsModal } from '@/components/admin/ActiveSessionsModal';
import { TestimonialModeration } from '@/components/admin/TestimonialModeration';

export default function AdminDashboardPage() {
  const router = useRouter();
  const { username, userId, isAdmin, isAuthenticated, isLoading: authLoading } = useAuth();
  const [isResetting, setIsResetting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showForbidden, setShowForbidden] = useState(false);
  const [analytics, setAnalytics] = useState<any>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);
  const [adminSectionsLoading, setAdminSectionsLoading] = useState(true);
  const [showSessionsModal, setShowSessionsModal] = useState(false);
  const [activeSessionsCount, setActiveSessionsCount] = useState<number | null>(null);

  // Debug logging
  console.log('Admin check - username:', username, 'userId:', userId, 'isAdmin:', isAdmin);

  // Fetch analytics data
  useEffect(() => {
    if (isAdmin && !authLoading) {
      fetchAnalytics();
      fetchActiveSessionsCount();
      // Set a minimum loading time to prevent flash
      const timer = setTimeout(() => {
        setAdminSectionsLoading(false);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [isAdmin, authLoading]);

  const fetchAnalytics = async () => {
    setAnalyticsLoading(true);
    try {
      const { data, error } = await apiClient.getAnalytics();
      if (data) {
        console.log('Analytics data received:', data);
        setAnalytics(data);
      } else {
        console.error('Failed to fetch analytics:', error);
      }
    } catch (err) {
      console.error('Error fetching analytics:', err);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const fetchActiveSessionsCount = async () => {
    try {
      const { data } = await apiClient.getActiveSessions();
      if (data) {
        setActiveSessionsCount(data.total_active);
      }
    } catch (err) {
      console.error('Error fetching active sessions:', err);
    }
  };

  // Redirect non-admin users
  useEffect(() => {
    if (!authLoading && isAuthenticated && !isAdmin) {
      // Show forbidden message for authenticated non-admin users
      setShowForbidden(true);
      // Redirect after 2 seconds
      const timer = setTimeout(() => {
        router.push('/dashboard');
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [authLoading, isAuthenticated, isAdmin, router]);

  const handleReset = async () => {
    setIsResetting(true);
    setError(null);
    setSuccess(null);

    try {
      const { data, error } = await apiClient.resetProgress();

      if (error) {
        setError(error);
        setIsResetting(false);
        setShowConfirm(false);
        return;
      }

      setSuccess('Progress reset successfully! Logging out...');
      
      // Log out the user to clear session
      await apiClient.logout();
      
      // Clear session storage
      sessionStorage.clear();
      
      // Redirect to home page after logout
      setTimeout(() => {
        window.location.href = '/';
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset progress');
      setIsResetting(false);
      setShowConfirm(false);
    }
  };

  // Show loading while checking auth (only on initial load)
  if (authLoading && !isAdmin) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-950 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  // Show forbidden message for authenticated non-admin users
  if (showForbidden) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-950">
        <NavbarWithAuth />
        <main className="pt-16 flex items-center justify-center min-h-[calc(100vh-4rem)]">
          <div className="max-w-md mx-auto px-4">
            <Card padding="lg">
              <div className="text-center py-8">
                <div className="mb-6">
                  <svg 
                    className="w-20 h-20 mx-auto text-red-500 dark:text-red-400" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
                    />
                  </svg>
                </div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                  403 - Access Denied
                </h1>
                <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
                  You don't have permission to access this page. Admin access is required.
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-500 mb-6">
                  Redirecting to dashboard...
                </p>
                <Spinner size="md" />
              </div>
            </Card>
          </div>
        </main>
      </div>
    );
  }

  // Don't render anything if not admin (will redirect)
  if (!isAdmin) {
    return null;
  }

  return (
    <AuthGuard>
      <div className="min-h-screen bg-white dark:bg-gray-950">
        <NavbarWithAuth />
        
        <main className="pt-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center space-x-3 mb-2">
                <svg 
                  className="w-8 h-8 text-amber-500 dark:text-amber-400" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" 
                  />
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" 
                  />
                </svg>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                  Admin Dashboard
                </h1>
              </div>
              <p className="text-gray-600 dark:text-gray-400">
                System administration and management tools
              </p>
            </div>

            {/* Success/Error Messages */}
            {success && (
              <div className="mb-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <p className="text-sm text-green-800 dark:text-green-200">{success}</p>
                </div>
              </div>
            )}

            {error && (
              <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Analytics Overview - Full Width */}
              <Card padding="lg" className="lg:col-span-2">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                    Platform Analytics
                  </h2>
                  <button
                    onClick={fetchAnalytics}
                    disabled={analyticsLoading}
                    className="text-sm text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 transition-colors disabled:opacity-50"
                  >
                    {analyticsLoading ? 'Loading...' : 'Refresh'}
                  </button>
                </div>
                
                {analyticsLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Spinner size="lg" />
                  </div>
                ) : analytics ? (
                  <div className="space-y-6">
                    {/* Key Metrics */}
                    <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                        <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                          {analytics.total_registered_users}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Total Registered
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                          All users who signed up
                        </div>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                        <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                          {analytics.users_completed_all}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Completed All
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                          Finished all 4 courses
                        </div>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                        <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                          {analytics.average_completion_rate}%
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Avg Completion
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                          Across engaged learners
                        </div>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                        <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                          {analytics.active_learners_7d}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Active Learners
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                          Last 7 days
                        </div>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                        <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                          {analytics.total_capstone_submissions}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Capstone Projects
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                          Total submissions
                        </div>
                      </div>
                      <button
                        onClick={() => setShowSessionsModal(true)}
                        className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 text-left hover:ring-2 hover:ring-teal-500/50 transition-all cursor-pointer"
                      >
                        <div className="text-2xl font-bold text-teal-600 dark:text-teal-400">
                          {activeSessionsCount !== null ? activeSessionsCount : '—'}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Active Sessions
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                          Unique users online
                        </div>
                      </button>
                    </div>

                    {/* Registration Timeline */}
                    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                        New User Registrations (Last 30 Days)
                      </h3>
                      {analytics.registration_timeline && analytics.registration_timeline.length > 0 ? (
                        <div className="relative">
                          <svg viewBox="0 0 800 300" className="w-full h-64" preserveAspectRatio="xMidYMid meet">
                            {/* Grid lines */}
                            <line x1="50" y1="250" x2="750" y2="250" stroke="currentColor" strokeWidth="1" className="text-gray-300 dark:text-gray-700" />
                            <line x1="50" y1="200" x2="750" y2="200" stroke="currentColor" strokeWidth="1" className="text-gray-300 dark:text-gray-700" strokeDasharray="4" />
                            <line x1="50" y1="150" x2="750" y2="150" stroke="currentColor" strokeWidth="1" className="text-gray-300 dark:text-gray-700" strokeDasharray="4" />
                            <line x1="50" y1="100" x2="750" y2="100" stroke="currentColor" strokeWidth="1" className="text-gray-300 dark:text-gray-700" strokeDasharray="4" />
                            <line x1="50" y1="50" x2="750" y2="50" stroke="currentColor" strokeWidth="1" className="text-gray-300 dark:text-gray-700" strokeDasharray="4" />
                            
                            {/* Y-axis */}
                            <line x1="50" y1="30" x2="50" y2="250" stroke="currentColor" strokeWidth="2" className="text-gray-400 dark:text-gray-600" />
                            
                            {/* X-axis */}
                            <line x1="50" y1="250" x2="750" y2="250" stroke="currentColor" strokeWidth="2" className="text-gray-400 dark:text-gray-600" />
                            
                            {/* Y-axis labels */}
                            {(() => {
                              const maxCount = Math.max(...analytics.registration_timeline.map((d: any) => d.count), 1);
                              const step = Math.ceil(maxCount / 4);
                              return [0, 1, 2, 3, 4].map(i => {
                                const value = i * step;
                                const y = 250 - (i * 50);
                                return (
                                  <text key={i} x="40" y={y + 5} textAnchor="end" className="text-xs fill-gray-600 dark:fill-gray-400">
                                    {value}
                                  </text>
                                );
                              });
                            })()}
                            
                            {/* Line path */}
                            {(() => {
                              const maxCount = Math.max(...analytics.registration_timeline.map((d: any) => d.count), 1);
                              const points = analytics.registration_timeline.map((d: any, i: number) => {
                                const x = 50 + (i * (700 / (analytics.registration_timeline.length - 1)));
                                const y = 250 - ((d.count / maxCount) * 200);
                                return `${x},${y}`;
                              }).join(' ');
                              
                              return (
                                <>
                                  <polyline
                                    points={points}
                                    fill="none"
                                    stroke="rgb(245, 158, 11)"
                                    strokeWidth="3"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                  />
                                  {/* Data points */}
                                  {analytics.registration_timeline.map((d: any, i: number) => {
                                    const x = 50 + (i * (700 / (analytics.registration_timeline.length - 1)));
                                    const y = 250 - ((d.count / maxCount) * 200);
                                    return (
                                      <g key={i}>
                                        <circle
                                          cx={x}
                                          cy={y}
                                          r="4"
                                          fill="rgb(245, 158, 11)"
                                          className="hover:r-6 transition-all"
                                        />
                                        {d.count > 0 && (
                                          <title>{`${d.date}: ${d.count} registration${d.count !== 1 ? 's' : ''}`}</title>
                                        )}
                                      </g>
                                    );
                                  })}
                                </>
                              );
                            })()}
                            
                            {/* X-axis labels (show every 5th day) */}
                            {analytics.registration_timeline.map((d: any, i: number) => {
                              if (i % 5 === 0 || i === analytics.registration_timeline.length - 1) {
                                const x = 50 + (i * (700 / (analytics.registration_timeline.length - 1)));
                                const dateObj = new Date(d.date);
                                const label = `${dateObj.getMonth() + 1}/${dateObj.getDate()}`;
                                return (
                                  <text
                                    key={i}
                                    x={x}
                                    y="270"
                                    textAnchor="middle"
                                    className="text-xs fill-gray-600 dark:fill-gray-400"
                                  >
                                    {label}
                                  </text>
                                );
                              }
                              return null;
                            })}
                          </svg>
                          <div className="mt-4 text-center">
                            <span className="inline-flex items-center text-sm text-gray-600 dark:text-gray-400">
                              <span className="w-3 h-3 bg-amber-500 rounded-full mr-2"></span>
                              New Registrations
                            </span>
                          </div>
                        </div>
                      ) : (
                        <div className="text-center text-gray-600 dark:text-gray-400 py-8">
                          No registration data available
                        </div>
                      )}
                    </div>

                    {/* Top Users */}
                    {analytics.completion_by_user && analytics.completion_by_user.length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                          Top Learners
                        </h3>
                        <div className="space-y-2">
                          {analytics.completion_by_user.slice(0, 5).map((user: any, index: number) => (
                            <div 
                              key={user.user_id}
                              className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                            >
                              <div className="flex items-center space-x-3">
                                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 font-semibold text-sm">
                                  {index + 1}
                                </div>
                                <div>
                                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                    {user.username}
                                  </div>
                                  <div className="text-xs text-gray-600 dark:text-gray-400">
                                    {user.completed} lessons completed
                                  </div>
                                </div>
                              </div>
                              <div className="flex items-center space-x-3">
                                <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                  <div 
                                    className="bg-amber-500 h-2 rounded-full transition-all duration-500"
                                    style={{ width: `${user.percentage}%` }}
                                  />
                                </div>
                                <div className="text-sm font-semibold text-gray-900 dark:text-gray-100 w-12 text-right">
                                  {user.percentage}%
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-12 text-gray-600 dark:text-gray-400">
                    No analytics data available
                  </div>
                )}
              </Card>

              {/* Testimonial Moderation - Full Width */}
              <Card padding="lg" className="lg:col-span-2">
                {adminSectionsLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Spinner size="lg" />
                  </div>
                ) : (
                  <TestimonialModeration />
                )}
              </Card>

              {/* Capstone Submissions - Full Width */}
              <Card padding="lg" className="lg:col-span-2">
                {adminSectionsLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Spinner size="lg" />
                  </div>
                ) : (
                  <CapstoneSubmissions />
                )}
              </Card>

              {/* User Search - Full Width */}
              <Card padding="lg" className="lg:col-span-2">
                {adminSectionsLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Spinner size="lg" />
                  </div>
                ) : (
                  <UserList />
                )}
              </Card>

              {/* Walkthrough Statistics - Full Width */}
              <Card padding="lg" className="lg:col-span-2">
                {adminSectionsLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Spinner size="lg" />
                  </div>
                ) : (
                  <WalkthroughStatistics />
                )}
              </Card>

              {/* Badge & Achievement Stats - Half Width */}
              <Card padding="lg">
                {adminSectionsLoading || analyticsLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Spinner size="lg" />
                  </div>
                ) : analytics?.badge_stats ? (
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                      Badge & Achievement Stats
                    </h2>
                    
                    <div className="grid grid-cols-2 gap-4 mb-6">
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                        <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                          {analytics.badge_stats.total_badges_earned}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Total Badges Earned
                        </div>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                        <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                          {analytics.badge_stats.unique_users_with_badges}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Users with Badges
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                        Most Earned Badges
                      </h3>
                      <div className="space-y-2">
                        {analytics.badge_stats.badge_distribution.slice(0, 5).map((badge: any) => (
                          <div key={badge.badge_id} className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-gray-800 last:border-0">
                            <span className="text-sm text-gray-900 dark:text-gray-100">{badge.badge_title}</span>
                            <span className="text-sm font-semibold text-amber-600 dark:text-amber-400">{badge.count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    No badge data available
                  </div>
                )}
              </Card>

              {/* Quiz Performance - Half Width */}
              <Card padding="lg">
                {adminSectionsLoading || analyticsLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Spinner size="lg" />
                  </div>
                ) : analytics?.quiz_stats ? (
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                      Quiz Performance
                    </h2>
                    
                    <div className="grid grid-cols-3 gap-4 mb-6">
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                        <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                          {analytics.quiz_stats.total_quiz_attempts}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Total Attempts
                        </div>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                        <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                          {analytics.quiz_stats.average_score}%
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Avg Score
                        </div>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                        <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                          {analytics.quiz_stats.perfect_scores}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Perfect Scores
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                        Most Challenging Quizzes
                      </h3>
                      <div className="space-y-2">
                        {analytics.quiz_stats.quiz_performance.map((quiz: any) => (
                          <div key={quiz.module_id} className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-gray-800 last:border-0">
                            <span className="text-sm text-gray-900 dark:text-gray-100 truncate flex-1">{quiz.module_id}</span>
                            <div className="flex items-center space-x-3">
                              <span className="text-xs text-gray-500 dark:text-gray-500">{quiz.attempts} attempts</span>
                              <span className="text-sm font-semibold text-red-600 dark:text-red-400">{quiz.avg_score}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    No quiz data available
                  </div>
                )}
              </Card>
            </div>
          </div>
        </main>

        {showSessionsModal && (
          <ActiveSessionsModal onClose={() => setShowSessionsModal(false)} />
        )}
      </div>
    </AuthGuard>
  );
}
