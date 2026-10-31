'use client';

import React, { useId, useRef } from 'react';

export interface TabItem {
  id: string;
  label: string;
  content: React.ReactNode;
}

export interface TabsProps {
  items: TabItem[];
  /** ID of the active tab (controlled). */
  activeId: string;
  onChange: (id: string) => void;
  /** Accessible name for the tablist. */
  ariaLabel?: string;
  className?: string;
}

/**
 * Accessible tabs with automatic activation.
 * Roving tabindex; ArrowLeft/ArrowRight (wrapping), Home and End move and select tabs.
 * Only the active panel's content is mounted; inactive panels stay in the DOM as hidden.
 */
export function Tabs({ items, activeId, onChange, ariaLabel, className = '' }: TabsProps) {
  const baseId = useId();
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);

  const tabId = (id: string) => `${baseId}-tab-${id}`;
  const panelId = (id: string) => `${baseId}-panel-${id}`;

  const focusAndSelect = (index: number) => {
    const item = items[index];
    if (!item) return;
    onChange(item.id);
    tabRefs.current[index]?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    const last = items.length - 1;
    switch (e.key) {
      case 'ArrowRight':
        e.preventDefault();
        focusAndSelect(index === last ? 0 : index + 1);
        break;
      case 'ArrowLeft':
        e.preventDefault();
        focusAndSelect(index === 0 ? last : index - 1);
        break;
      case 'Home':
        e.preventDefault();
        focusAndSelect(0);
        break;
      case 'End':
        e.preventDefault();
        focusAndSelect(last);
        break;
    }
  };

  return (
    <div className={className}>
      <div
        role="tablist"
        aria-label={ariaLabel}
        className="flex gap-2 mb-6 overflow-x-auto border-b border-gray-200 dark:border-gray-800"
      >
        {items.map((item, index) => {
          const selected = item.id === activeId;
          return (
            <button
              key={item.id}
              ref={(el) => {
                tabRefs.current[index] = el;
              }}
              id={tabId(item.id)}
              type="button"
              role="tab"
              aria-selected={selected}
              aria-controls={panelId(item.id)}
              tabIndex={selected ? 0 : -1}
              onClick={() => onChange(item.id)}
              onKeyDown={(e) => handleKeyDown(e, index)}
              className={`min-h-[44px] min-w-[44px] px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 -mb-px transition-colors focus:outline-hidden focus-visible:ring-2 focus-visible:ring-amber-500 ${
                selected
                  ? 'border-amber-500 text-amber-600 dark:text-amber-400'
                  : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
              }`}
            >
              {item.label}
            </button>
          );
        })}
      </div>
      {items.map((item) => {
        const selected = item.id === activeId;
        return (
          <div
            key={item.id}
            id={panelId(item.id)}
            role="tabpanel"
            aria-labelledby={tabId(item.id)}
            hidden={!selected}
            tabIndex={0}
          >
            {selected ? item.content : null}
          </div>
        );
      })}
    </div>
  );
}
