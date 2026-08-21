/**
 * Static learning path metadata for public preview pages and sitemap generation.
 * Groups modules by learning path from modules.json.
 */

import modulesData from '@/lib/data/modules.json';

export interface LearningPathPreviewData {
  /** URL-safe slug */
  slug: string;
  /** Display name */
  name: string;
  /** Ordered modules in this path */
  modules: Array<{
    title: string;
    /** Slug for the module preview page */
    previewSlug: string;
    pageCount: number;
    order: number;
  }>;
  /** Total lessons across all modules */
  totalLessons: number;
  /** Total modules */
  moduleCount: number;
}

function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

/** Build learning path data from modules.json, grouped and sorted */
function buildLearningPaths(): LearningPathPreviewData[] {
  const pathMap = new Map<string, LearningPathPreviewData>();

  for (const mod of modulesData) {
    const pathName = mod.learningPath;
    const pathSlug = slugify(pathName);

    if (!pathMap.has(pathSlug)) {
      pathMap.set(pathSlug, {
        slug: pathSlug,
        name: pathName,
        modules: [],
        totalLessons: 0,
        moduleCount: 0,
      });
    }

    const path = pathMap.get(pathSlug)!;
    path.modules.push({
      title: mod.title,
      previewSlug: mod.id.replace(/\//g, '--'),
      pageCount: mod.pages.length,
      order: mod.order,
    });
    path.totalLessons += mod.pages.length;
    path.moduleCount += 1;
  }

  // Sort modules within each path by order
  for (const path of pathMap.values()) {
    path.modules.sort((a, b) => a.order - b.order);
  }

  // Sort paths by the minimum order of their modules
  return Array.from(pathMap.values()).sort(
    (a, b) => (a.modules[0]?.order ?? 0) - (b.modules[0]?.order ?? 0)
  );
}

export const learningPathsMetadata = buildLearningPaths();

/** Look up a learning path by its URL slug */
export function getLearningPathBySlug(slug: string): LearningPathPreviewData | undefined {
  return learningPathsMetadata.find((lp) => lp.slug === slug);
}
