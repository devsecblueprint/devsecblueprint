'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Accordion } from '@/components/ui/Accordion';
import type { AccordionItem } from '@/components/ui/Accordion';
import { useAdminContext } from './AdminDashboardProvider';
import { SectionErrorBoundary } from './SectionErrorBoundary';

// Admin components
import { UserSearch } from '@/components/admin/UserSearch';
import { CapstoneSubmissions } from '@/components/admin/CapstoneSubmissions';
import { TestimonialModeration } from '@/components/admin/TestimonialModeration';
import { BroadcastManagement } from '@/components/admin/BroadcastManagement';
import { WalkthroughStatistics } from '@/components/admin/WalkthroughStatistics';
import { WalkthroughAccessTiers } from '@/components/admin/WalkthroughAccessTiers';
import { RegistryStatus } from '@/components/admin/RegistryStatus';
import { ModuleHealth } from '@/components/admin/ModuleHealth';
import { ExportData } from '@/components/admin/ExportData';

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
 * AdministrativeTools organizes all admin management components into 5
 * collapsible categories using the Accordion component.
 *
 * Categories:
 * 1. Member Management – UserSearch, membership controls (AdminUserDiscordPanel accessible via UserProfileModal)
 * 2. Reviews – CapstoneSubmissions, TestimonialModeration
 * 3. Communications – BroadcastManagement
 * 4. Learning & Content – WalkthroughStatistics, WalkthroughAccessTiers, RegistryStatus, ModuleHealth, badge/quiz stats
 * 5. System – ActiveSessionsModal trigger, ExportData, maintenance functions
 *
 * Default opens the first category (Member Management) via `defaultOpenId`.
 * Each category section div has an id for scroll-into-view navigation from NeedsAttentionPanel.
 */
export function AdministrativeTools() {
  const { analytics, openSessionsModal } = useAdminContext();

  const badgeStats = analytics?.badge_stats;
  const quizStats = analytics?.quiz_stats;

  const accordionItems: AccordionItem[] = [
    {
      id: 'member-management',
      trigger: 'Member Management',
      content: (
        <div id="member-management" className="space-y-6">
          <SectionErrorBoundary name="User Search">
            <UserSearch />
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
      id: 'communications',
      trigger: 'Communications',
      content: (
        <div id="communications" className="space-y-6">
          <SectionErrorBoundary name="Broadcast Management">
            <BroadcastManagement />
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
          <SectionErrorBoundary name="Registry Status">
            <RegistryStatus />
          </SectionErrorBoundary>
          <SectionErrorBoundary name="Module Health">
            <ModuleHealth />
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
    {
      id: 'system',
      trigger: 'System',
      content: (
        <div id="system" className="space-y-6">
          <div className="flex flex-wrap gap-3">
            <Button
              onClick={openSessionsModal}
              variant="secondary"
              className="min-h-[44px]"
            >
              View Active Sessions
            </Button>
          </div>
          <SectionErrorBoundary name="Export Data">
            <ExportData />
          </SectionErrorBoundary>
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
    </Card>
  );
}
