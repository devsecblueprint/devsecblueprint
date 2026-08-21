/**
 * Static module metadata for public preview pages and sitemap generation.
 * Derived from modules.json with URL-safe slugs for routing.
 */

import modulesData from '@/lib/data/modules.json';

export interface ModulePreviewData {
  /** URL-safe slug (module id with '/' replaced by '--') */
  slug: string;
  /** Original module id */
  id: string;
  title: string;
  learningPath: string;
  order: number;
  pageCount: number;
  pageTitles: string[];
}

export const modulesMetadata: ModulePreviewData[] = modulesData.map((m) => ({
  slug: m.id.replace(/\//g, '--'),
  id: m.id,
  title: m.title,
  learningPath: m.learningPath,
  order: m.order,
  pageCount: m.pages.length,
  pageTitles: m.pages.map((p) => p.title),
}));

/** Look up a module by its URL slug */
export function getModuleBySlug(slug: string): ModulePreviewData | undefined {
  return modulesMetadata.find((m) => m.slug === slug);
}
