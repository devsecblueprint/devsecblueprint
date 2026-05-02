'use client';

import { useEffect, useState } from 'react';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkRehype from 'remark-rehype';
import rehypeHighlight from 'rehype-highlight';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';
import type { Schema } from 'hast-util-sanitize';
import rehypeStringify from 'rehype-stringify';

interface MarkdownRendererProps {
  markdown: string;
}

/**
 * Custom sanitization schema that extends the default to allow
 * code highlighting classes while still preventing XSS.
 */
const sanitizeSchema: Schema = {
  ...defaultSchema,
  attributes: {
    ...defaultSchema.attributes,
    code: [
      ...(defaultSchema.attributes?.code || []),
      ['className', /^hljs-/],
    ],
    span: [
      ...(defaultSchema.attributes?.span || []),
      ['className', /^hljs-/],
    ],
  },
};

/**
 * MarkdownRenderer — renders raw markdown into sanitized semantic HTML.
 *
 * Uses the remark/rehype pipeline (already in the project) with rehype-sanitize
 * to prevent XSS. Produces semantic HTML elements:
 * - Headings: h1–h6
 * - Emphasis: strong, em
 * - Code: pre/code with syntax highlighting
 * - Links: a (with rel="noopener noreferrer" on external links)
 * - Lists: ol/ul/li
 */
export default function MarkdownRenderer({ markdown }: MarkdownRendererProps) {
  const [html, setHtml] = useState<string>('');

  useEffect(() => {
    let cancelled = false;

    async function render() {
      const result = await unified()
        .use(remarkParse)
        .use(remarkGfm)
        .use(remarkRehype)
        .use(rehypeHighlight, { detect: true, ignoreMissing: true })
        .use(rehypeSanitize, sanitizeSchema)
        .use(rehypeStringify)
        .process(markdown);

      if (!cancelled) {
        setHtml(String(result));
      }
    }

    render();

    return () => {
      cancelled = true;
    };
  }, [markdown]);

  return (
    <div
      className="prose prose-invert max-w-none"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
