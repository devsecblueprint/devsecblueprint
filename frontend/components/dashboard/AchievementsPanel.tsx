'use client';

import { Badge as BadgeType } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { SkeletonBadgeCard } from '@/components/ui/Skeleton';

/**
 * AchievementsPanel Component
 *
 * Displays all earned and locked badges in a compact grid.
 * Earned badges at full opacity (1.0), locked badges at 0.4 opacity.
 * Includes text labels ("Earned" / "Locked") to distinguish status without relying on color alone.
 * Shows skeleton loading state (6 cards) while loading.
 * Shows empty state on error (no raw error messages).
 *
 * Requirements: 5.6, 5.7, 5.10, 5.12, 9.8
 */

export interface AchievementsPanelProps {
  badges: BadgeType[];
  isLoading: boolean;
  error: string | null;
}

export function AchievementsPanel({ badges, isLoading, error }: AchievementsPanelProps) {
  return (
    <section aria-labelledby="achievements-heading">
      <div className="flex items-center justify-between mb-4">
        <h2
          id="achievements-heading"
          className="text-2xl font-bold text-gray-900 dark:text-gray-100"
        >
          Achievements
        </h2>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonBadgeCard key={i} />
          ))}
        </div>
      ) : error ? (
        <Card className="flex flex-col items-center justify-center py-8 text-center">
          <span className="text-3xl mb-2" aria-hidden="true">
            🏆
          </span>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            No badges to display right now.
          </p>
        </Card>
      ) : badges.length === 0 ? (
        <Card className="flex flex-col items-center justify-center py-8 text-center">
          <span className="text-3xl mb-2" aria-hidden="true">
            🏆
          </span>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Start learning to earn your first badge!
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {badges.map((badge) => (
            <Card
              key={badge.id}
              padding="sm"
              className={`flex flex-col items-center text-center transition-opacity ${
                badge.earned ? 'opacity-100' : 'opacity-40'
              }`}
            >
              <span className="text-2xl mb-2" aria-hidden="true">
                {badge.icon}
              </span>
              <span className="text-xs font-medium text-gray-900 dark:text-gray-100 mb-1 line-clamp-2">
                {badge.title}
              </span>
              <Badge
                variant={badge.earned ? 'success' : 'default'}
                size="sm"
              >
                {badge.earned ? 'Earned' : 'Locked'}
              </Badge>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}
