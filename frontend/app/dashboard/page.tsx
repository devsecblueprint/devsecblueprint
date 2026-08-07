'use client';

import { useState, useEffect } from 'react';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { WelcomeModal } from '@/components/WelcomeModal';
import { BadgeNotification } from '@/components/BadgeNotification';
import { BroadcastModal } from '@/components/BroadcastModal';
import { AuthGuard } from '@/components/AuthGuard';
import { useAuth } from '@/lib/hooks/useAuth';
import { useBadges } from '@/lib/hooks/useBadges';
import { useAllProgress } from '@/lib/hooks/useAllProgress';
import { useLastActiveLesson } from '@/lib/hooks/useLastActiveLesson';
import { apiClient } from '@/lib/api';
import { deriveMemberRole } from '@/components/dashboard/utils';
import {
  DashboardHeader,
  BuilderJourneyWidget,
  ContinueLearningCard,
  LearningSummaryGrid,
  LearningPathsSection,
  WalkthroughsSection,
  ActivityAchievementsSection,
  MembershipDiscordCommunitySection,
} from '@/components/dashboard';
import type { ContributorRole, BroadcastItem } from '@/lib/types';

export default function DashboardPage() {
  // Top-level hooks
  const { userId, username, isAdmin } = useAuth();
  const { badges, isLoading: badgesLoading, error: badgesError, newlyEarnedBadges, clearNewBadge } = useBadges();
  const { progress, isLoading: progressLoading } = useAllProgress();
  const { pageSlug: lastActiveSlug, isLoading: lastActiveLessonLoading } = useLastActiveLesson();

  // Modal state
  const [showWelcome, setShowWelcome] = useState(false);
  const [showBroadcastModal, setShowBroadcastModal] = useState(false);
  const [unreadBroadcasts, setUnreadBroadcasts] = useState<BroadcastItem[]>([]);

  // Profile state
  const [hasCheckedProfile, setHasCheckedProfile] = useState(false);
  const [contributorRole, setContributorRole] = useState<ContributorRole | null>(null);

  // One-time profile check for is_new_user and contributor_role
  useEffect(() => {
    const checkUserProfile = async () => {
      if (!userId || hasCheckedProfile) return;
      try {
        const { data } = await apiClient.getUserProfile();
        if (data?.is_new_user) {
          const hasSeenWelcome = sessionStorage.getItem('hasSeenWelcome');
          if (!hasSeenWelcome) {
            setShowWelcome(true);
          }
        }
        if (data?.contributor_role) {
          setContributorRole(data.contributor_role);
        }
      } catch (err) {
        console.error('Failed to fetch user profile:', err);
      } finally {
        setHasCheckedProfile(true);
      }
    };
    checkUserProfile();
  }, [userId, hasCheckedProfile]);

  // Fetch unread broadcasts — only when welcome modal is not showing
  useEffect(() => {
    const fetchBroadcasts = async () => {
      if (!userId || showWelcome) return;
      try {
        const { data } = await apiClient.getUnreadBroadcasts();
        if (data?.broadcasts && data.broadcasts.length > 0) {
          setUnreadBroadcasts(data.broadcasts);
          setShowBroadcastModal(true);
        }
      } catch (err) {
        console.error('Failed to fetch broadcasts:', err);
      }
    };
    fetchBroadcasts();
  }, [userId, showWelcome]);

  const handleCloseWelcome = () => {
    setShowWelcome(false);
    sessionStorage.setItem('hasSeenWelcome', 'true');
  };

  // Modal priority: at most one overlay at a time
  // SessionExpiryModal handled by AuthProvider (no changes needed here)
  const showBroadcast = !showWelcome && showBroadcastModal && unreadBroadcasts.length > 0;
  const showBadge = !showWelcome && !showBroadcast && newlyEarnedBadges.length > 0;

  const role = deriveMemberRole(isAdmin, contributorRole);

  return (
    <AuthGuard>
      {/* Modals - priority order enforced by conditional rendering */}
      <WelcomeModal
        isOpen={showWelcome}
        onClose={handleCloseWelcome}
        username={username || undefined}
      />
      {showBadge && (
        <BadgeNotification badge={newlyEarnedBadges[0]} onClose={clearNewBadge} />
      )}
      {showBroadcast && (
        <BroadcastModal
          broadcasts={unreadBroadcasts}
          onAllDismissed={() => {
            setShowBroadcastModal(false);
            setUnreadBroadcasts([]);
          }}
        />
      )}

      <div className="min-h-screen bg-white dark:bg-gray-950">
        <NavbarWithAuth />
        <main className="pt-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
            <div className="space-y-6 sm:space-y-12">
              <DashboardHeader
                username={username}
                isAdmin={isAdmin}
                contributorRole={contributorRole}
                isLoading={!hasCheckedProfile}
              />
              <BuilderJourneyWidget />
              <ContinueLearningCard
                progress={progress}
                progressLoading={progressLoading}
                lastActiveSlug={lastActiveSlug}
                lastActiveLessonLoading={lastActiveLessonLoading}
              />
              <LearningSummaryGrid />
              <LearningPathsSection
                progress={progress}
                isLoading={progressLoading}
              />
              <WalkthroughsSection />
              <ActivityAchievementsSection
                badges={badges}
                badgesLoading={badgesLoading}
                badgesError={badgesError}
              />
              <MembershipDiscordCommunitySection role={role} isAdmin={isAdmin} />
            </div>
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
