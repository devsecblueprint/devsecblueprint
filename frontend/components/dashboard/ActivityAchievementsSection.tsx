'use client';

import { Badge } from '@/lib/types';
import { ActivityTimeline } from '@/components/dashboard/ActivityTimeline';
import { AchievementsPanel } from '@/components/dashboard/AchievementsPanel';

/**
 * ActivityAchievementsSection Component
 *
 * Two-column responsive layout wrapper that composes ActivityTimeline and AchievementsPanel.
 * Side by side at >= 768px (md breakpoint), stacks to single column below 768px.
 *
 * Requirements: 5.1
 */

export interface ActivityAchievementsSectionProps {
  badges: Badge[];
  badgesLoading: boolean;
  badgesError: string | null;
}

export function ActivityAchievementsSection({
  badges,
  badgesLoading,
  badgesError,
}: ActivityAchievementsSectionProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
      <ActivityTimeline />
      <AchievementsPanel
        badges={badges}
        isLoading={badgesLoading}
        error={badgesError}
      />
    </div>
  );
}
