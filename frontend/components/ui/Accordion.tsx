'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';

export interface AccordionItem {
  id: string;
  trigger: string;
  content: React.ReactNode;
}

export interface AccordionProps {
  items: AccordionItem[];
  defaultOpenId?: string;
  className?: string;
}

/**
 * Accessible accordion component with single-open behavior and full keyboard navigation.
 * Supports deep linking via `defaultOpenId`, ARIA attributes for screen readers,
 * and respects `prefers-reduced-motion: reduce` by disabling transitions.
 *
 * @param items - Array of accordion items with id, trigger text, and content
 * @param defaultOpenId - ID of the item to open on mount (for hash-based deep linking)
 * @param className - Additional CSS classes for the container
 */
export function Accordion({ items, defaultOpenId, className = '' }: AccordionProps) {
  const [openId, setOpenId] = useState<string | null>(defaultOpenId ?? null);
  const triggerRefs = useRef<(HTMLButtonElement | null)[]>([]);

  // Sync defaultOpenId changes (e.g. when hash changes after mount)
  useEffect(() => {
    if (defaultOpenId !== undefined) {
      setOpenId(defaultOpenId);
    }
  }, [defaultOpenId]);

  const handleToggle = useCallback((id: string) => {
    setOpenId((prev) => (prev === id ? null : id));
  }, []);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLButtonElement>, index: number) => {
      const count = items.length;
      let nextIndex: number | null = null;

      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          nextIndex = (index + 1) % count;
          break;
        case 'ArrowUp':
          event.preventDefault();
          nextIndex = (index - 1 + count) % count;
          break;
        case 'Home':
          event.preventDefault();
          nextIndex = 0;
          break;
        case 'End':
          event.preventDefault();
          nextIndex = count - 1;
          break;
        case 'Enter':
        case ' ':
          event.preventDefault();
          handleToggle(items[index].id);
          break;
        default:
          return;
      }

      if (nextIndex !== null) {
        triggerRefs.current[nextIndex]?.focus();
      }
    },
    [items, handleToggle]
  );

  return (
    <div className={`divide-y divide-gray-200 dark:divide-gray-800 ${className}`}>
      {items.map((item, index) => {
        const isOpen = openId === item.id;
        const triggerId = `accordion-trigger-${item.id}`;
        const panelId = `accordion-panel-${item.id}`;

        return (
          <div key={item.id}>
            <h3>
              <button
                ref={(el) => { triggerRefs.current[index] = el; }}
                id={triggerId}
                type="button"
                aria-expanded={isOpen}
                aria-controls={panelId}
                onClick={() => handleToggle(item.id)}
                onKeyDown={(e) => handleKeyDown(e, index)}
                className={`flex w-full items-center justify-between py-4 px-4 text-left text-base font-medium text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-950 rounded-lg transition-colors ${
                  isOpen
                    ? 'bg-gray-100 dark:bg-gray-800'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
                }`}
              >
                <span>{item.trigger}</span>
                <svg
                  className={`h-5 w-5 shrink-0 text-gray-500 dark:text-gray-400 transform motion-safe:transition-transform motion-safe:duration-200 ${
                    isOpen ? 'rotate-180' : ''
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
            </h3>
            <div
              id={panelId}
              role="region"
              aria-labelledby={triggerId}
              hidden={!isOpen}
              className="overflow-hidden"
            >
              <div className="px-4 pb-4 text-gray-700 dark:text-gray-300">
                {item.content}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
