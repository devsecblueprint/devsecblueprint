'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';

export interface CategoryCardProps {
  name: string;
  slug: string;
  description: string;
  icon: string;
  onClick: () => void;
}

/**
 * Maps icon identifiers to inline SVG elements (24x24px).
 */
function CategoryIcon({ icon }: { icon: string }) {
  const className = 'h-6 w-6 text-amber-500 dark:text-amber-400';

  switch (icon) {
    case 'info-circle':
      return (
        <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="16" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12.01" y2="8" />
        </svg>
      );
    case 'book-open':
      return (
        <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z" />
          <path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z" />
        </svg>
      );
    case 'star':
      return (
        <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
        </svg>
      );
    case 'users':
      return (
        <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 00-3-3.87" />
          <path d="M16 3.13a4 4 0 010 7.75" />
        </svg>
      );
    case 'briefcase':
      return (
        <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
          <path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16" />
        </svg>
      );
    case 'credit-card':
      return (
        <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <rect x="1" y="4" width="22" height="16" rx="2" ry="2" />
          <line x1="1" y1="10" x2="23" y2="10" />
        </svg>
      );
    case 'git-merge':
      return (
        <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx="18" cy="18" r="3" />
          <circle cx="6" cy="6" r="3" />
          <path d="M6 21V9a9 9 0 009 9" />
        </svg>
      );
    case 'terminal':
      return (
        <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <polyline points="4 17 10 11 4 5" />
          <line x1="12" y1="19" x2="20" y2="19" />
        </svg>
      );
    default:
      return (
        <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="10" />
        </svg>
      );
  }
}

/**
 * A clickable category card that displays an icon, heading, and description.
 * Used in the FAQ CategoryNav grid to allow users to jump to a category section.
 *
 * - Minimum 44x44px touch target
 * - Keyboard accessible: focusable, activatable via Enter/Space
 * - Hover/focus visual states using existing design tokens
 *
 * @param name - Category display name
 * @param slug - Category slug (used for identification)
 * @param description - Short description of the category
 * @param icon - Icon identifier mapped to SVG component
 * @param onClick - Callback invoked when the card is activated (click, Enter, or Space)
 */
export function CategoryCard({ name, slug, description, icon, onClick }: CategoryCardProps) {
  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onClick();
    }
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      aria-label={`Navigate to ${name} category`}
      className="min-h-[44px] min-w-[44px] cursor-pointer focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-950 rounded-2xl transition-all hover:scale-[1.02] hover:shadow-xl"
    >
      <Card className="h-full transition-colors hover:border-amber-400 dark:hover:border-amber-500" padding="md">
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-3">
            <CategoryIcon icon={icon} />
            <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
              {name}
            </h3>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
            {description}
          </p>
        </div>
      </Card>
    </div>
  );
}
