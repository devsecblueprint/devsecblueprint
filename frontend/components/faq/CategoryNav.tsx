'use client';

import React from 'react';
import { FAQCategory } from '@/lib/data/faq';
import { CategoryCard } from './CategoryCard';

export interface CategoryNavProps {
  categories: FAQCategory[];
  onCategoryClick: (slug: string) => void;
}

/**
 * Responsive grid of CategoryCard components for FAQ category navigation.
 *
 * - 4 columns on viewports >= 1024px
 * - 2 columns on viewports 640-1023px
 * - Single-column stacked on viewports < 640px
 * - Hidden (returns null) when categories array is empty
 *
 * @param categories - Filtered categories (only those with visible questions)
 * @param onCategoryClick - Callback with category slug when a card is clicked
 */
export function CategoryNav({ categories, onCategoryClick }: CategoryNavProps) {
  if (categories.length === 0) {
    return null;
  }

  return (
    <nav aria-label="FAQ categories" className="mb-12">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {categories.map((category) => (
          <CategoryCard
            key={category.slug}
            name={category.name}
            slug={category.slug}
            description={category.description}
            icon={category.icon}
            onClick={() => onCategoryClick(category.slug)}
          />
        ))}
      </div>
    </nav>
  );
}
