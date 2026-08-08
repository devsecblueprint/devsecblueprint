'use client';

import React, { useState, useCallback } from 'react';
import { trackFAQEvent } from '@/lib/utils/faq-analytics';

export interface CopyLinkButtonProps {
  slug: string;
}

/**
 * A small copy-link button that copies the deep link URL for a specific FAQ question
 * to the clipboard. Shows a brief "Copied!" tooltip on success.
 *
 * Designed to be placed inside an AccordionItem trigger row and appear on
 * hover/focus of the parent (via group utility). Also becomes visible on its
 * own focus for keyboard accessibility.
 */
export function CopyLinkButton({ slug }: CopyLinkButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(
    async (e: React.MouseEvent<HTMLButtonElement>) => {
      // Prevent the click from toggling the parent accordion
      e.stopPropagation();

      const url = `${window.location.origin}/about/faq#${slug}`;

      try {
        await navigator.clipboard.writeText(url);
        setCopied(true);
        trackFAQEvent({ type: 'copy_link', questionSlug: slug });

        setTimeout(() => {
          setCopied(false);
        }, 2000);
      } catch {
        // Graceful fallback — Clipboard API may be unavailable in some contexts.
        // No crash; simply do nothing visible to the user.
      }
    },
    [slug]
  );

  return (
    <span className="relative inline-flex items-center">
      <button
        type="button"
        onClick={handleCopy}
        aria-label="Copy link to this question"
        className={[
          'inline-flex items-center justify-center w-8 h-8 md:w-8 md:h-8 min-w-[44px] min-h-[44px] md:min-w-0 md:min-h-0 rounded-md',
          'text-gray-500 hover:text-amber-500 dark:text-gray-400 dark:hover:text-amber-400',
          'opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 focus:opacity-100',
          'transition-opacity duration-150',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2',
        ].join(' ')}
      >
        {/* Chain link icon */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="w-4 h-4"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 001.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {/* Copied tooltip */}
      {copied && (
        <span
          role="status"
          className={[
            'absolute -top-8 left-1/2 -translate-x-1/2',
            'px-2 py-1 text-xs font-medium rounded shadow-sm',
            'bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900',
            'whitespace-nowrap pointer-events-none',
            'animate-fade-in',
          ].join(' ')}
        >
          Copied!
        </span>
      )}
    </span>
  );
}
