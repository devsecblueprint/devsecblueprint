'use client';

import React from 'react';
import { FAQCategory } from '@/lib/data/faq';
import { MultiAccordion, AccordionItemData } from './MultiAccordion';
import { AnswerContent } from './AnswerContent';

export interface FAQCategorySectionProps {
  category: FAQCategory;
  filteredQuestionSlugs: string[];
  expandedIds: Set<string>;
  onToggle: (slug: string) => void;
  onQuestionExpand: (questionSlug: string, categorySlug: string) => void;
}

/**
 * Renders a single FAQ category section with heading, description, and accordion.
 *
 * - Anchor element with `id={category.slug}` enables deep-link scrolling and category navigation.
 * - When `filteredQuestionSlugs` is empty, all questions in the category are displayed.
 * - When `filteredQuestionSlugs` has values, only matching questions are shown.
 * - Calls `onQuestionExpand` when a question transitions from collapsed to expanded (for analytics).
 *
 * Validates: Requirements 7.4, 7.5, 9.1
 */
export function FAQCategorySection({
  category,
  filteredQuestionSlugs,
  expandedIds,
  onToggle,
  onQuestionExpand,
}: FAQCategorySectionProps) {
  const visibleQuestions =
    filteredQuestionSlugs.length === 0
      ? category.questions
      : category.questions.filter((q) =>
          filteredQuestionSlugs.includes(q.slug)
        );

  const items: AccordionItemData[] = visibleQuestions.map((q) => ({
    id: q.slug,
    trigger: q.question,
    content: <AnswerContent answer={q.answer} links={q.links} />,
  }));

  const handleToggle = (slug: string) => {
    // If the item is not currently expanded, it's about to be expanded — fire analytics
    if (!expandedIds.has(slug)) {
      onQuestionExpand(slug, category.slug);
    }
    onToggle(slug);
  };

  return (
    <section id={category.slug} className="scroll-mt-24 pt-8 sm:pt-12">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        {category.name}
      </h2>
      <p className="text-gray-600 dark:text-gray-400 mb-6">
        {category.description}
      </p>
      <MultiAccordion
        items={items}
        expandedIds={expandedIds}
        onToggle={handleToggle}
      />
    </section>
  );
}
