'use client';

import { useState, useEffect } from 'react';
import { Accordion } from '@/components/ui/Accordion';
import { FAQ_CATEGORIES } from '@/lib/data/faq';

function renderAnswerWithLinks(text: string): React.ReactNode {
  const urlPattern = /(https?:\/\/[^\s]+)/g;
  const parts = text.split(urlPattern);

  return parts.map((part, i) => {
    if (part.match(/^https?:\/\//)) {
      return (
        <a
          key={i}
          href={part}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary-500 dark:text-primary-400 underline hover:text-primary-600 dark:hover:text-primary-300"
        >
          {part}
        </a>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

export default function FAQClient() {
  const [defaultOpenId, setDefaultOpenId] = useState<string | undefined>(undefined);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const hash = window.location.hash.slice(1);
    if (hash) {
      const allSlugs = FAQ_CATEGORIES.flatMap((cat) =>
        cat.questions.map((q) => q.slug)
      );
      if (allSlugs.includes(hash)) {
        setDefaultOpenId(hash);
        // Scroll to the matching panel within 500ms
        setTimeout(() => {
          const el = document.getElementById(`accordion-trigger-${hash}`);
          el?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
      }
      // Invalid hash: all panels collapsed, scroll at top (default behavior)
    }
    setIsReady(true);
  }, []);

  // Don't render until we've checked the hash to avoid flash of incorrect state
  if (!isReady) {
    return null;
  }

  return (
    <div className="max-w-4xl mx-auto px-6">
      {FAQ_CATEGORIES.map((category) => (
        <section key={category.slug} className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            {category.name}
          </h2>
          <Accordion
            items={category.questions.map((q) => ({
              id: q.slug,
              trigger: q.question,
              content: <p>{renderAnswerWithLinks(q.answer)}</p>,
            }))}
            defaultOpenId={defaultOpenId}
          />
        </section>
      ))}
    </div>
  );
}
