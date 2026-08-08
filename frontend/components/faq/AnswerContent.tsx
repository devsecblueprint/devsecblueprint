import React from 'react';
import Link from 'next/link';
import { CrossLink } from '@/lib/data/faq';

export interface AnswerContentProps {
  answer: string;
  links?: CrossLink[];
}

/**
 * Renders FAQ answer text with inline URL detection and optional structured cross-links.
 *
 * - Detects plain-text URLs (http/https) and renders them as clickable links.
 * - Renders structured CrossLink objects as a "Related:" section below the answer.
 *   Internal links use Next.js Link for client-side navigation; external links open
 *   in a new tab with `rel="noopener noreferrer"`.
 * - Uses readable text formatting: max-w-prose, text-base (16px), leading-relaxed.
 */
export function AnswerContent({ answer, links }: AnswerContentProps) {
  return (
    <div className="max-w-prose text-base leading-relaxed text-gray-700 dark:text-gray-300">
      <p>{renderAnswerWithLinks(answer)}</p>

      {links && links.length > 0 && (
        <div className="mt-3">
          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
            Related:{' '}
          </span>
          {links.map((link, index) => (
            <React.Fragment key={link.href}>
              {index > 0 && (
                <span className="text-gray-400 dark:text-gray-500"> · </span>
              )}
              {link.external ? (
                <a
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-500 dark:text-primary-400 underline hover:text-primary-600 dark:hover:text-primary-300 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 rounded"
                >
                  {link.text}
                </a>
              ) : (
                <Link
                  href={link.href}
                  className="text-primary-500 dark:text-primary-400 underline hover:text-primary-600 dark:hover:text-primary-300 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 rounded"
                >
                  {link.text}
                </Link>
              )}
            </React.Fragment>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Detects inline URLs in plain text and renders them as clickable links.
 * Uses regex to split text on http/https URLs and wraps matches in anchor tags.
 */
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
          className="text-primary-500 dark:text-primary-400 underline hover:text-primary-600 dark:hover:text-primary-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 rounded"
        >
          {part}
        </a>
      );
    }
    return <span key={i}>{part}</span>;
  });
}
