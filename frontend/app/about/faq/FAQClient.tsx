'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { SearchBar, CategoryNav, FAQCategorySection } from '@/components/faq';
import { FAQ_CATEGORIES, FAQCategory } from '@/lib/data/faq';
import { trackFAQEvent } from '@/lib/utils/faq-analytics';

/**
 * Filters FAQ categories based on a search query.
 * Returns all categories (with empty matchingSlugs) when query is blank.
 * When a query is provided, returns only categories with matching questions.
 */
function filterFAQ(
  categories: FAQCategory[],
  query: string
): { category: FAQCategory; matchingSlugs: string[] }[] {
  if (!query.trim()) {
    return categories.map((cat) => ({ category: cat, matchingSlugs: [] }));
  }
  const normalizedQuery = query.toLowerCase().trim();
  return categories
    .map((category) => {
      const matchingSlugs = category.questions
        .filter(
          (q) =>
            q.question.toLowerCase().includes(normalizedQuery) ||
            q.answer.toLowerCase().includes(normalizedQuery)
        )
        .map((q) => q.slug);
      return { category, matchingSlugs };
    })
    .filter((result) => result.matchingSlugs.length > 0);
}

/**
 * FAQClient — client-side orchestrator for the FAQ page.
 *
 * Manages search filtering, multi-open accordion state, deep-link hash navigation,
 * and analytics event emission. Composes SearchBar, CategoryNav, and FAQCategorySection.
 */
export default function FAQClient() {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  // Deep-link hash detection on mount
  useEffect(() => {
    const hash = window.location.hash.slice(1);
    if (!hash) return;

    // Check if hash matches a question slug
    const allQuestions = FAQ_CATEGORIES.flatMap((cat) => cat.questions);
    const matchingQuestion = allQuestions.find((q) => q.slug === hash);
    if (matchingQuestion) {
      setExpandedIds((prev) => new Set([...prev, hash]));
      setTimeout(() => {
        document.getElementById(`question-${hash}`)?.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
        });
      }, 100);
      return;
    }

    // Check if hash matches a category slug
    const matchingCategory = FAQ_CATEGORIES.find((cat) => cat.slug === hash);
    if (matchingCategory) {
      setTimeout(() => {
        document.getElementById(hash)?.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
        });
      }, 100);
    }
  }, []);

  // Memoized search filtering — recalculates when searchQuery changes
  const filteredResults = useMemo(
    () => filterFAQ(FAQ_CATEGORIES, searchQuery),
    [searchQuery]
  );

  // Total result count for SearchBar (sum of matching questions across visible categories)
  const totalResultCount = useMemo(() => {
    if (!searchQuery.trim()) {
      return FAQ_CATEGORIES.flatMap((cat) => cat.questions).length;
    }
    return filteredResults.reduce(
      (sum, result) => sum + result.matchingSlugs.length,
      0
    );
  }, [filteredResults, searchQuery]);

  // Search query change handler with analytics
  const handleSearchChange = useCallback((query: string) => {
    setSearchQuery(query);

    if (query.trim()) {
      const results = filterFAQ(FAQ_CATEGORIES, query);
      const count = results.reduce((sum, r) => sum + r.matchingSlugs.length, 0);

      if (count === 0) {
        trackFAQEvent({ type: 'search_no_results', query });
      } else {
        trackFAQEvent({
          type: 'search_performed',
          query,
          resultCount: count,
        });
      }
    }
  }, []);

  // Category card click handler
  const handleCategoryClick = useCallback((slug: string) => {
    trackFAQEvent({ type: 'category_selected', categorySlug: slug });
    document.getElementById(slug)?.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    });
  }, []);

  // Toggle accordion item (multi-open: add/remove from set)
  const handleToggle = useCallback((slug: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) {
        next.delete(slug);
      } else {
        next.add(slug);
      }
      return next;
    });
  }, []);

  // Analytics for question expand
  const handleQuestionExpand = useCallback(
    (questionSlug: string, categorySlug: string) => {
      trackFAQEvent({
        type: 'question_expanded',
        questionSlug,
        categorySlug,
      });
    },
    []
  );

  const hasResults = filteredResults.length > 0;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6">
      {/* Search bar */}
      <SearchBar
        value={searchQuery}
        onChange={handleSearchChange}
        resultCount={totalResultCount}
      />

      {/* Category navigation cards */}
      {hasResults && (
        <CategoryNav
          categories={filteredResults.map((r) => r.category)}
          onCategoryClick={handleCategoryClick}
        />
      )}

      {/* FAQ category sections */}
      {hasResults ? (
        filteredResults.map(({ category, matchingSlugs }) => (
          <FAQCategorySection
            key={category.slug}
            category={category}
            filteredQuestionSlugs={matchingSlugs}
            expandedIds={expandedIds}
            onToggle={handleToggle}
            onQuestionExpand={handleQuestionExpand}
          />
        ))
      ) : (
        <div className="text-center py-16">
          <p className="text-gray-500 dark:text-gray-400 text-lg">
            No questions found. Try a different search term.
          </p>
        </div>
      )}
    </div>
  );
}
