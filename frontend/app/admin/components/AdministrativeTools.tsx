'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Accordion } from '@/components/ui/Accordion';
import type { AccordionItem } from '@/components/ui/Accordion';
import { useAdminContext } from './AdminDashboardProvider';
import { SectionErrorBoundary } from './SectionErrorBoundary';

// Admin components
import { UserList } from '@/components/admin/UserList';
import { CapstoneSubmissions } from '@/components/admin/CapstoneSubmissions';
import { TestimonialModeration } from '@/components/admin/TestimonialModeration';
import { WalkthroughStatistics } from '@/components/admin/WalkthroughStatistics';
import { WalkthroughAccessTiers } from '@/components/admin/WalkthroughAccessTiers';
import { ExportData } from '@/components/admin/ExportData';

// Certification components
import { CertificationStats } from './certifications/CertificationStats';
import { CertificationCandidates } from './certifications/CertificationCandidates';
import { PathwayManagement } from './certifications/PathwayManagement';
import { CandidateDetailModal } from './certifications/CandidateDetailModal';

/**
 * Fallback message when a category has no tools available due to permissions.
 */
function NoToolsAvailable() {
  return (
    <p className="text-sm text-gray-500 dark:text-gray-400 italic py-2">
      No tools available
    </p>
  );
}

/**
 * AdministrativeTools organizes admin management components into collapsible
 * categories using the Accordion component.
 *
 * Categories:
 * 1. Member Management – UserList with paginated search, UserProfileModal (role management, AdminUserDiscordPanel), ExportData
 * 2. Reviews – CapstoneSubmissions, TestimonialModeration
 * 3. Learning & Content – WalkthroughStatistics, WalkthroughAccessTiers, badge/quiz stats
 *
 * Certifications is also rendered as its own category. Broadcasts live on /admin/broadcasts,
 * and the Active Sessions modal is opened from the KPI card.
 *
 * Default opens the first category (Member Management) via `defaultOpenId`.
 * Each category section div has an id for scroll-into-view navigation from NeedsAttentionPanel.
 */
export function AdministrativeTools() {
  const { analytics } = useAdminContext();
  const [selectedCandidate, setSelectedCandidate] = useState<{ userId: string; pathwayId: string } | null>(null);

  const badgeStats = analytics?.badge_stats;
  const quizStats = analytics?.quiz_stats;

  const accordionItems: AccordionItem[] = [
    {
      id: 'member-management',
      trigger: 'Member Management',
      content: (
        <div id="member-management" className="space-y-6">
          <SectionErrorBoundary name="User Management">
            <UserList />
          </SectionErrorBoundary>
          <SectionErrorBoundary name="Export Data">
            <ExportData />
          </SectionErrorBoundary>
        </div>
      ),
    },
    {
      id: 'reviews',
      trigger: 'Reviews',
      content: (
        <div id="reviews" className="space-y-6">
          <SectionErrorBoundary name="Capstone Submissions">
            <CapstoneSubmissions />
          </SectionErrorBoundary>
          <SectionErrorBoundary name="Testimonial Moderation">
            <TestimonialModeration />
          </SectionErrorBoundary>
        </div>
      ),
    },
    {
      id: 'certifications',
      trigger: 'Certifications',
      content: (
        <div id="certifications" className="space-y-6">
          <SectionErrorBoundary name="Certification Stats">
            <CertificationStats />
          </SectionErrorBoundary>
          <SectionErrorBoundary name="Certification Candidates">
            <CertificationCandidates onSelectCandidate={(userId, pathwayId) => setSelectedCandidate({ userId, pathwayId })} />
          </SectionErrorBoundary>
          <SectionErrorBoundary name="Pathway Management">
            <PathwayManagement />
          </SectionErrorBoundary>
        </div>
      ),
    },
    {
      id: 'learning-content',
      trigger: 'Learning & Content',
      content: (
        <div id="learning-content" className="space-y-6">
          <SectionErrorBoundary name="Walkthrough Statistics">
            <WalkthroughStatistics />
          </SectionErrorBoundary>
          <SectionErrorBoundary name="Walkthrough Access Tiers">
            <WalkthroughAccessTiers />
          </SectionErrorBoundary>
          {/* Badge & Quiz Statistics */}
          {(badgeStats || quizStats) && (
            <div className="space-y-4">
              {badgeStats && (
                <div className="rounded-xl border border-gray-200 dark:border-gray-800 p-4">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
                    Badge Statistics
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Total Earned</span>
                      <p className="font-semibold text-gray-900 dark:text-gray-100">
                        {badgeStats.total_badges_earned}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Unique Users</span>
                      <p className="font-semibold text-gray-900 dark:text-gray-100">
                        {badgeStats.unique_users_with_badges}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Badge Types</span>
                      <p className="font-semibold text-gray-900 dark:text-gray-100">
                        {badgeStats.badge_distribution?.length ?? 0}
                      </p>
                    </div>
                  </div>
                </div>
              )}
              {quizStats && (
                <div className="rounded-xl border border-gray-200 dark:border-gray-800 p-4">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
                    Quiz Statistics
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Total Attempts</span>
                      <p className="font-semibold text-gray-900 dark:text-gray-100">
                        {quizStats.total_quiz_attempts}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Average Score</span>
                      <p className="font-semibold text-gray-900 dark:text-gray-100">
                        {quizStats.average_score}%
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Perfect Scores</span>
                      <p className="font-semibold text-gray-900 dark:text-gray-100">
                        {quizStats.perfect_scores}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ),
    },
  ];

  return (
    <Card>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        Administrative Tools
      </h2>
      <Accordion
        items={accordionItems}
        defaultOpenId="member-management"
      />
      {selectedCandidate && (
        <CandidateDetailModal
          isOpen={!!selectedCandidate}
          onClose={() => setSelectedCandidate(null)}
          userId={selectedCandidate.userId}
          pathwayId={selectedCandidate.pathwayId}
          onActionComplete={() => setSelectedCandidate(null)}
        />
      )}
    </Card>
  );
}
