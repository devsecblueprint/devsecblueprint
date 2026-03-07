'use client';

import { useState, useEffect } from 'react';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { DashboardStats } from '@/components/features/DashboardStats';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { CenteredSpinner } from '@/components/ui/Spinner';
import { WelcomeModal } from '@/components/WelcomeModal';
import { BadgeNotification } from '@/components/BadgeNotification';
import { QuickLinksSection } from '@/components/features/QuickLinksSection';
import { 
  SkeletonStatCard, 
  SkeletonBadgeCard, 
  SkeletonActivityCard, 
  SkeletonLearningCard 
} from '@/components/ui/Skeleton';
import { LEARNING_PATHS } from '@/lib/constants';
import { useAuth } from '@/lib/hooks/useAuth';
import { useUserStats } from '@/lib/hooks/useUserStats';
import { useRecentActivities } from '@/lib/hooks/useRecentActivities';
import { useBadges } from '@/lib/hooks/useBadges';
import { AuthGuard } from '@/components/AuthGuard';
import { useAllProgress } from '@/lib/hooks/useAllProgress';
import { getAllCourses } from '@/lib/course-utils';
import { apiClient } from '@/lib/api';

export default function DashboardPage() {
  const { userId, avatarUrl, username } = useAuth();
  const { currentStreak, longestStreak, overallCompletion, quizzesPassed, walkthroughsCompleted, isLoading: statsLoading } = useUserStats();
  const { activities, isLoading: activitiesLoading } = useRecentActivities();
  const { badges, isLoading: badgesLoading, newlyEarnedBadges, clearNewBadge } = useBadges();
  const { progress, isLoading: progressLoading } = useAllProgress();
  const [showWelcomeModal, setShowWelcomeModal] = useState(false);
  const [hasCheckedProfile, setHasCheckedProfile] = useState(false);

  // Debug logging for modal state
  useEffect(() => {
    console.log('[WelcomeModal] showWelcomeModal state changed:', showWelcomeModal);
  }, [showWelcomeModal]);

  // Check if user is new and show welcome modal
  useEffect(() => {
    const checkUserProfile = async () => {
      if (!userId || hasCheckedProfile) return;

      try {
        console.log('[WelcomeModal] Fetching user profile for userId:', userId);
        const { data, error } = await apiClient.getUserProfile();
        
        console.log('[WelcomeModal] Profile response:', { data, error });
        
        if (data && data.is_new_user) {
          // Check if we've already shown the welcome modal in this session
          const hasSeenWelcome = sessionStorage.getItem('hasSeenWelcome');
          
          console.log('[WelcomeModal] User is new, hasSeenWelcome:', hasSeenWelcome);
          
          if (!hasSeenWelcome) {
            console.log('[WelcomeModal] Showing welcome modal');
            setShowWelcomeModal(true);
          }
        } else {
          console.log('[WelcomeModal] User is not new or data missing');
        }
      } catch (err) {
        console.error('[WelcomeModal] Failed to fetch user profile:', err);
      } finally {
        setHasCheckedProfile(true);
      }
    };

    checkUserProfile();
  }, [userId, hasCheckedProfile]);

  const handleCloseWelcomeModal = () => {
    setShowWelcomeModal(false);
    // Mark as seen in session storage so it doesn't show again during this session
    sessionStorage.setItem('hasSeenWelcome', 'true');
  };

  // Prepare stats for DashboardStats component
  const stats = [
    {
      label: 'Quizzes Passed',
      value: statsLoading ? '...' : `${quizzesPassed}`,
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    },
    {
      label: 'Walkthroughs Completed',
      value: statsLoading ? '...' : `${walkthroughsCompleted}`,
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
        </svg>
      )
    },
    {
      label: 'Overall Completion',
      value: statsLoading ? '...' : `${overallCompletion}%`,
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    }
  ];

  // Use real recent activities or show empty state
  const recentActivities = activities.length > 0 ? activities : [];
  
  // Check if user is new (no progress at all)
  const isNewUser = !statsLoading && quizzesPassed === 0 && walkthroughsCompleted === 0 && overallCompletion === 0;
  
  // Check if user has completed everything (only check when data is loaded)
  const isComplete = !statsLoading && overallCompletion === 100;
  
  // Check if all data is still loading
  const isInitialLoading = statsLoading && activitiesLoading && badgesLoading;

  // Get courses with progress data to show incomplete ones
  const allCourses = getAllCourses(progress);
  const incompleteCourses = allCourses.filter(course => 
    course.learningPath !== 'Walkthroughs' && course.percentComplete < 100
  ).slice(0, 2);
  
  const continueLearning = incompleteCourses.length > 0 
    ? incompleteCourses.map(course => ({
        id: `${course.learningPath}/${course.topic}`,
        title: course.title,
        description: `${course.completedPages} of ${course.totalPages} lessons completed`,
        moduleCount: course.totalPages,
        slug: course.firstPageSlug
      }))
    : [];

  return (
    <AuthGuard>
      {/* Welcome Modal */}
      <WelcomeModal 
        isOpen={showWelcomeModal} 
        onClose={handleCloseWelcomeModal}
        username={username || undefined}
      />

      {/* Badge Notification */}
      {newlyEarnedBadges.length > 0 && (
        <BadgeNotification
          badge={newlyEarnedBadges[0]}
          onClose={clearNewBadge}
        />
      )}

      <div className="min-h-screen bg-white dark:bg-gray-950">
        {/* Navbar */}
        <NavbarWithAuth />

      {/* Main Content - Add top padding to account for fixed navbar */}
      <main className="pt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
          {/* Global Loading State */}
          {isInitialLoading ? (
            <div className="space-y-8">
              {/* Welcome Header Skeleton */}
              <div className="mb-8 sm:mb-12">
                <div className="flex items-center space-x-3 sm:space-x-4 mb-2">
                  <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-gray-200 dark:bg-gray-800 animate-pulse" />
                  <div className="space-y-2">
                    <div className="h-8 w-48 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
                    <div className="h-4 w-64 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
                  </div>
                </div>
              </div>

              {/* Stats Skeleton */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <SkeletonStatCard />
                <SkeletonStatCard />
                <SkeletonStatCard />
              </div>

              {/* Continue Learning Skeleton */}
              <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-8">
                <CenteredSpinner size="lg" />
              </div>

              {/* Badges Skeleton */}
              <div>
                <div className="h-6 w-32 bg-gray-200 dark:bg-gray-800 rounded animate-pulse mb-6" />
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 sm:gap-4">
                  <SkeletonBadgeCard />
                  <SkeletonBadgeCard />
                  <SkeletonBadgeCard />
                  <SkeletonBadgeCard />
                  <SkeletonBadgeCard />
                </div>
              </div>

              {/* Activities Skeleton */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8">
                <div>
                  <div className="h-6 w-40 bg-gray-200 dark:bg-gray-800 rounded animate-pulse mb-6" />
                  <div className="space-y-4">
                    <SkeletonLearningCard />
                    <SkeletonLearningCard />
                  </div>
                </div>
                <div>
                  <div className="h-6 w-48 bg-gray-200 dark:bg-gray-800 rounded animate-pulse mb-6" />
                  <div className="space-y-4">
                    <SkeletonActivityCard />
                    <SkeletonActivityCard />
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <>
          {/* Welcome Header */}
          <div className="mb-8 sm:mb-12">
            <div className="flex items-center space-x-3 sm:space-x-4 mb-2">
              {/* User Avatar */}
              {avatarUrl ? (
                <img 
                  src={avatarUrl} 
                  alt="User avatar"
                  className="w-12 h-12 sm:w-16 sm:h-16 rounded-full border-2 border-gray-300 dark:border-gray-800 flex-shrink-0"
                />
              ) : (
                <div className="flex items-center justify-center w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-gray-100 dark:bg-gray-900 border-2 border-gray-300 dark:border-gray-800 flex-shrink-0">
                  <svg 
                    className="w-6 h-6 sm:w-8 sm:h-8 text-gray-600 dark:text-gray-400" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" 
                    />
                  </svg>
                </div>
              )}
              <div className="min-w-0">
                <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 truncate">
                  Welcome back!
                </h1>
                <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 mt-1 truncate">
                  {new Date().toLocaleDateString('en-US', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </p>
              </div>
            </div>
          </div>

          {/* Dashboard Stats */}
          <div className="mb-8 sm:mb-12">
            {statsLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <SkeletonStatCard />
                <SkeletonStatCard />
                <SkeletonStatCard />
              </div>
            ) : (
              <DashboardStats stats={stats} />
            )}
          </div>

          {/* Continue Where You Left Off / Completion Celebration */}
          <section className="mb-8 sm:mb-12">
            <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
              {isNewUser ? 'Start Your Learning Journey' : isComplete ? 'Congratulations!' : 'Continue Where You Left Off'}
            </h2>
            <Card padding="lg">
              {isNewUser ? (
                // New user welcome message
                <div className="text-center py-8">
                  <div className="mb-6">
                    <svg 
                      className="w-16 h-16 mx-auto text-amber-500 dark:text-amber-400" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth={2} 
                        d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" 
                      />
                    </svg>
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                    Welcome to The DevSec Blueprint!
                  </h3>
                  <p className="text-base text-gray-600 dark:text-gray-400 mb-6 max-w-2xl mx-auto">
                    You're all set to begin your journey into DevSecOps and Cloud Security Development. 
                    Start with any learning path below, and your progress will be tracked automatically.
                  </p>
                  <div className="flex flex-col sm:flex-row gap-3 justify-center">
                    <a
                      href="/courses"
                      className="inline-flex items-center justify-center px-6 py-3 bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
                    >
                      <span>Browse All Courses</span>
                      <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                      </svg>
                    </a>
                    <a
                      href="/learn/welcome"
                      className="inline-flex items-center justify-center px-6 py-3 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 font-semibold rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
                    >
                      Read Welcome Message
                    </a>
                  </div>
                </div>
              ) : isComplete ? (
                // 100% completion celebration
                <div className="text-center py-8">
                  <div className="mb-6">
                    <svg 
                      className="w-20 h-20 mx-auto text-green-500 dark:text-green-400" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth={2} 
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" 
                      />
                    </svg>
                  </div>
                  <h3 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                    You've Completed All Available Courses! 🎉
                  </h3>
                  <p className="text-lg text-gray-600 dark:text-gray-400 mb-6 max-w-2xl mx-auto">
                    Amazing work! You've mastered all the current content. Check back soon for new courses, 
                    or review what you've learned to reinforce your knowledge.
                  </p>
                  <div className="flex flex-col sm:flex-row gap-3 justify-center">
                    <a
                      href="/courses"
                      className="inline-flex items-center justify-center px-6 py-3 bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
                    >
                      <span>Review Courses</span>
                      <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </a>
                  </div>
                </div>
              ) : (
                // Existing user - show last accessed content
                progressLoading ? (
                  // Show loading state while progress is being fetched
                  <div className="flex items-center justify-center py-12">
                    <CenteredSpinner size="lg" />
                  </div>
                ) : continueLearning.length > 0 ? (
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <Badge variant="default" size="sm">
                        {continueLearning[0]?.id?.split('/')[0]?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </Badge>
                      <span className="text-xs text-gray-500 dark:text-gray-500">•</span>
                      <span className="text-xs text-gray-500 dark:text-gray-500">
                        Last accessed 2 hours ago
                      </span>
                    </div>
                    <h3 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                      {continueLearning[0]?.title}
                    </h3>
                    <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 mb-4">
                      {continueLearning[0]?.description}
                    </p>
                    <div className="flex items-center space-x-4">
                      <div className="flex-1 max-w-xs">
                        <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                          <span>Progress</span>
                          <span>{incompleteCourses[0]?.percentComplete ?? 0}%</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-2">
                          <div 
                            className="bg-amber-500 dark:bg-amber-400 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${incompleteCourses[0]?.percentComplete ?? 0}%` }}
                          />
                        </div>
                      </div>
                      <span className="text-xs text-gray-600 dark:text-gray-400 whitespace-nowrap">
                        {incompleteCourses[0]?.completedPages ?? 0} of {incompleteCourses[0]?.totalPages ?? 0} sections
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-col sm:flex-row gap-3">
                    <a
                      href={continueLearning[0]?.slug}
                      className="inline-flex items-center justify-center px-6 py-3 bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
                    >
                      <span>Continue Learning</span>
                      <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                      </svg>
                    </a>
                    <a
                      href="/courses"
                      className="inline-flex items-center justify-center px-6 py-3 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 font-semibold rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
                    >
                      View All Courses
                    </a>
                  </div>
                </div>
                ) : (
                  // No incomplete courses - show browse message
                  <div className="text-center py-8">
                    <div className="mb-6">
                      <svg 
                        className="w-16 h-16 mx-auto text-amber-500 dark:text-amber-400" 
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path 
                          strokeLinecap="round" 
                          strokeLinejoin="round" 
                          strokeWidth={2} 
                          d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" 
                        />
                      </svg>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                      Ready to Start Learning?
                    </h3>
                    <p className="text-base text-gray-600 dark:text-gray-400 mb-6 max-w-2xl mx-auto">
                      Browse our courses and start your DevSecOps journey today.
                    </p>
                    <a
                      href="/courses"
                      className="inline-flex items-center justify-center px-6 py-3 bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
                    >
                      <span>Browse All Courses</span>
                      <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                      </svg>
                    </a>
                  </div>
                )
              )}
            </Card>
          </section>

          {/* Walkthroughs Section */}
          <section className="mb-8 sm:mb-12">
            <div className="flex items-center justify-between mb-4 sm:mb-6">
              <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-gray-100">
                Hands-On Walkthroughs
              </h2>
              <a
                href="/walkthroughs"
                className="inline-flex items-center px-4 py-2 bg-amber-500 dark:bg-amber-400 text-gray-900 text-sm font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
              >
                <span>View All Walkthroughs</span>
                <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </a>
            </div>
            <Card padding="lg">
              <div className="text-center py-8">
                <div className="mb-6">
                  <svg 
                    className="w-16 h-16 mx-auto text-amber-500 dark:text-amber-400" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" 
                    />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                  Practice with Real-World Projects
                </h3>
                <p className="text-base text-gray-600 dark:text-gray-400 mb-6 max-w-2xl mx-auto">
                  Explore curated code repositories and hands-on labs that demonstrate DevSecOps concepts 
                  through practical implementations. Each walkthrough includes complete documentation and working examples.
                </p>
                <a
                  href="/walkthroughs"
                  className="inline-flex items-center justify-center px-6 py-3 bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
                >
                  <span>Browse Walkthroughs</span>
                  <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </a>
              </div>
            </Card>
          </section>

          {/* Community & Engagement Quick Links Section */}
          <section className="mb-8 sm:mb-12">
            <QuickLinksSection />
          </section>

          {/* Badges Grid */}
          <section className="mb-8 sm:mb-12">
            <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
              Badges
            </h2>
            {badgesLoading ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 sm:gap-4">
                <SkeletonBadgeCard />
                <SkeletonBadgeCard />
                <SkeletonBadgeCard />
                <SkeletonBadgeCard />
                <SkeletonBadgeCard />
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 sm:gap-4">
                {badges.map((badge) => (
                  <Card 
                    key={badge.id} 
                    padding="md"
                    className={!badge.earned ? 'opacity-50' : ''}
                  >
                    <div className="flex flex-col items-center text-center">
                      <div className="text-4xl mb-3">
                        {badge.icon}
                      </div>
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1">
                        {badge.title}
                      </h3>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                        {badge.description}
                      </p>
                      {badge.earned ? (
                        <Badge variant="success" size="sm">
                          Earned
                        </Badge>
                      ) : (
                        <Badge variant="default" size="sm">
                          Locked
                        </Badge>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </section>

          {/* Continue Learning & Recently Completed */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8">
            {/* Continue Learning Section */}
            <section>
              <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
                {isComplete ? 'All Courses Complete' : 'Continue Learning'}
              </h2>
              {isComplete ? (
                <Card padding="md">
                  <div className="text-center py-8">
                    <div className="mb-4">
                      <svg 
                        className="w-16 h-16 mx-auto text-green-500 dark:text-green-400" 
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path 
                          strokeLinecap="round" 
                          strokeLinejoin="round" 
                          strokeWidth={2} 
                          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" 
                        />
                      </svg>
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                      All Caught Up!
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                      You've completed all available courses. Check back for new content!
                    </p>
                    <a
                      href="/courses"
                      className="inline-flex items-center justify-center px-4 py-2 bg-amber-500 dark:bg-amber-400 text-gray-900 text-sm font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500"
                    >
                      Browse Courses
                    </a>
                  </div>
                </Card>
              ) : (
                <div className="space-y-4">
                  {continueLearning.map((path) => (
                    <Card key={path.id} padding="md">
                      <a 
                        href={path.slug || `/learn/${path.id}`}
                        className="flex items-start justify-between group"
                      >
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2 group-hover:text-amber-500 dark:group-hover:text-amber-400 transition-colors">
                            {path.title}
                          </h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                            {path.description}
                          </p>
                          <div className="flex items-center space-x-2">
                            <Badge variant="default" size="sm">
                              {path.moduleCount} modules
                            </Badge>
                          </div>
                        </div>
                        <div 
                          className="ml-4 p-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-amber-500 dark:text-amber-400 group-hover:text-amber-600 dark:group-hover:text-amber-300 transition-colors rounded-lg group-hover:bg-gray-100 dark:group-hover:bg-gray-800"
                          aria-label={`Continue ${path.title}`}
                        >
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
                              d="M9 5l7 7-7 7" 
                            />
                          </svg>
                        </div>
                      </a>
                    </Card>
                  ))}
                </div>
              )}
            </section>

            {/* Recently Completed Section */}
            <section>
              <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
                Recently Completed
              </h2>
              {activitiesLoading ? (
                <div className="space-y-4">
                  <SkeletonActivityCard />
                  <SkeletonActivityCard />
                </div>
              ) : recentActivities.length === 0 ? (
                <Card padding="md">
                  <div className="text-center text-gray-600 dark:text-gray-400 py-8">
                    No completed activities yet. Start learning to see your progress here!
                  </div>
                </Card>
              ) : (
                <div className="space-y-4">
                  {recentActivities.map((activity) => (
                    <Card key={activity.id} padding="md">
                      <div className="flex items-center space-x-4">
                        <div className="flex-shrink-0">
                          <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 border border-green-300 dark:border-green-700 flex items-center justify-center">
                            <svg 
                              className="w-5 h-5 text-green-600 dark:text-green-400" 
                              fill="none" 
                              stroke="currentColor" 
                              viewBox="0 0 24 24"
                              aria-hidden="true"
                            >
                              <path 
                                strokeLinecap="round" 
                                strokeLinejoin="round" 
                                strokeWidth={2} 
                                d="M5 13l4 4L19 7" 
                              />
                            </svg>
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 truncate">
                            {activity.title}
                          </h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {activity.path}
                          </p>
                        </div>
                        <div className="flex-shrink-0">
                          <span className="text-xs text-gray-500 dark:text-gray-500">
                            {activity.relativeTime}
                          </span>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </section>
          </div>
            </>
          )}
        </div>
      </main>
      </div>
    </AuthGuard>
  );
}
