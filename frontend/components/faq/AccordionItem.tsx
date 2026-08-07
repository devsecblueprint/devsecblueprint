'use client';

import React from 'react';
import { CopyLinkButton } from './CopyLinkButton';

export interface AccordionItemProps {
  id: string;
  trigger: string;
  content: React.ReactNode;
  isExpanded: boolean;
  onToggle: () => void;
}

/**
 * Individual expandable FAQ question/answer item with full accessibility support.
 * Supports multi-open behavior (controlled by parent), deep link scrolling via
 * `id="question-{id}"`, copy-link affordance, and smooth expand/collapse animation.
 *
 * @param id - Unique slug identifier for the question (used for deep linking and ARIA)
 * @param trigger - The question text displayed on the trigger button
 * @param content - The answer content rendered in the expandable panel
 * @param isExpanded - Whether the panel is currently expanded
 * @param onToggle - Callback to toggle expanded state
 */
export function AccordionItem({ id, trigger, content, isExpanded, onToggle }: AccordionItemProps) {
  const triggerId = `accordion-trigger-${id}`;
  const panelId = `accordion-panel-${id}`;

  const handleKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onToggle();
    }
  };

  return (
    <div id={`question-${id}`} className="border-b border-gray-200 dark:border-gray-800">
      <h3>
        <div className="group flex items-center">
          <button
            id={triggerId}
            type="button"
            aria-expanded={isExpanded}
            aria-controls={panelId}
            onClick={onToggle}
            onKeyDown={handleKeyDown}
            className="flex w-full min-h-[44px] items-center justify-between py-4 px-4 text-left text-base font-medium text-gray-900 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-800/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-400 focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-gray-950 rounded-lg transition-colors"
          >
            <span className="pr-4">{trigger}</span>
            <svg
              className={`h-5 w-5 shrink-0 text-gray-500 dark:text-gray-400 transform motion-safe:transition-transform motion-safe:duration-200 ${
                isExpanded ? 'rotate-180' : ''
              }`}
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
                clipRule="evenodd"
              />
            </svg>
          </button>
          <div className="opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity">
            <CopyLinkButton slug={id} />
          </div>
        </div>
      </h3>
      <div
        id={panelId}
        role="region"
        aria-labelledby={triggerId}
        className={`grid motion-safe:transition-[grid-template-rows] motion-safe:duration-200 ease-in-out ${
          isExpanded ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
        }`}
      >
        <div className="overflow-hidden">
          <div className="px-4 pt-2 pb-4 text-gray-700 dark:text-gray-300">
            {content}
          </div>
        </div>
      </div>
    </div>
  );
}
