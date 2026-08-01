'use client';

import Link from 'next/link';
import { Card } from '@/components/ui/Card';

const MEMBERSHIP_HANDBOOK_URL = 'https://docs.google.com/document/d/1tV61uuOEs268hmhaZHxu-dPsbpAps3c8/edit?usp=drive_link&ouid=108753897807977150001&rtpof=true&sd=true';

/**
 * MembershipCard Component
 *
 * Displays the member's current role/tier with contextual content.
 * - Free: tier label, description, single contextual upgrade link to /pricing
 * - Builder: tier label, "Active" status, premium description, "Manage Membership" link
 * - Scholar/Contributor: role name label, "Active" status, premium description, no upgrade prompt
 * - Admin: role display, "Active" status, admin description, no upgrade prompt
 * - Defaults to Free when role cannot be determined
 * - No time-limited urgency, discount percentages, or modal pop-ups
 *
 * Requirements: 6.2, 6.3, 6.8, 6.9, 13.1, 13.2, 13.5, 13.6
 */

export type MemberRole = 'free' | 'builder' | 'scholar' | 'contributor' | 'admin';

export interface MembershipCardProps {
  role: MemberRole;
  isAdmin: boolean;
}

interface TierConfig {
  label: string;
  description: string;
  showActiveStatus: boolean;
  actionLink?: { href: string; label: string };
  handbookLink?: string;
}

function getTierConfig(role: MemberRole): TierConfig {
  switch (role) {
    case 'builder':
      return {
        label: 'Builder',
        description: 'Premium access to all courses, walkthroughs, and resources.',
        showActiveStatus: true,
        actionLink: { href: '/settings/subscription', label: 'Manage Membership' },
        handbookLink: MEMBERSHIP_HANDBOOK_URL,
      };
    case 'scholar':
      return {
        label: 'Scholar',
        description: 'Premium access to all courses, walkthroughs, and resources.',
        showActiveStatus: true,
        handbookLink: MEMBERSHIP_HANDBOOK_URL,
      };
    case 'contributor':
      return {
        label: 'Contributor',
        description: 'Premium access to all courses, walkthroughs, and resources.',
        showActiveStatus: true,
        handbookLink: MEMBERSHIP_HANDBOOK_URL,
      };
    case 'admin':
      return {
        label: 'Admin',
        description: 'Full administrative access to platform management and all content.',
        showActiveStatus: true,
        handbookLink: MEMBERSHIP_HANDBOOK_URL,
      };
    case 'free':
    default:
      return {
        label: 'Free',
        description: 'Access to free content and community resources.',
        showActiveStatus: false,
        actionLink: { href: '/pricing', label: 'Explore Builder \u2192' },
      };
  }
}

export function MembershipCard({ role, isAdmin }: MembershipCardProps) {
  const validRoles: MemberRole[] = ['free', 'builder', 'scholar', 'contributor', 'admin'];
  const effectiveRole: MemberRole = validRoles.includes(role) ? role : 'free';

  // If isAdmin is true, override to admin display
  const displayRole: MemberRole = isAdmin ? 'admin' : effectiveRole;
  const config = getTierConfig(displayRole);

  return (
    <Card>
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Membership
          </h3>
          {config.showActiveStatus && (
            <span className="inline-flex items-center gap-1.5 text-xs font-medium text-green-700 dark:text-green-400">
              <span
                className="w-2 h-2 rounded-full bg-green-500"
                aria-hidden="true"
              />
              Active
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400">
            {config.label}
          </span>
        </div>

        <p className="text-sm text-gray-600 dark:text-gray-400">
          {config.description}
        </p>

        {config.handbookLink && (
          <a
            href={config.handbookLink}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-amber-500 dark:hover:text-amber-400 transition-colors"
          >
            <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            Membership Handbook
            <svg className="w-3.5 h-3.5 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        )}

        {config.actionLink && (
          <Link
            href={config.actionLink.href}
            className="inline-flex items-center text-sm font-medium text-amber-500 dark:text-amber-400 hover:text-amber-600 dark:hover:text-amber-300 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 rounded"
          >
            {config.actionLink.label}
          </Link>
        )}
      </div>
    </Card>
  );
}
