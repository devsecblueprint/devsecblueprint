'use client';

import React from 'react';
import { AccordionItem } from './AccordionItem';

export interface AccordionItemData {
  id: string;
  trigger: string;
  content: React.ReactNode;
}

export interface MultiAccordionProps {
  items: AccordionItemData[];
  expandedIds: Set<string>;
  onToggle: (id: string) => void;
}

/**
 * Multi-open accordion component that allows multiple items to be expanded simultaneously.
 * Fully controlled — no internal state; the parent manages the expanded set via
 * `expandedIds` and `onToggle` props.
 *
 * @param items - Array of accordion items with id, trigger text, and content
 * @param expandedIds - Set of item IDs currently expanded
 * @param onToggle - Callback invoked when an item is toggled (parent adds/removes from set)
 */
export function MultiAccordion({ items, expandedIds, onToggle }: MultiAccordionProps) {
  return (
    <div className="divide-y divide-gray-200 dark:divide-gray-800">
      {items.map((item) => (
        <AccordionItem
          key={item.id}
          id={item.id}
          trigger={item.trigger}
          content={item.content}
          isExpanded={expandedIds.has(item.id)}
          onToggle={() => onToggle(item.id)}
        />
      ))}
    </div>
  );
}
