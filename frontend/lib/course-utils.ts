import modulesData from '@/lib/data/modules.json';
import { Module } from '@/lib/types';

export interface CourseProgress {
  learningPath: string;
  topic: string;
  title: string;
  totalPages: number;
  completedPages: number;
  percentComplete: number;
  firstPageSlug: string;
  lastActiveSlug: string;
  modules: Module[];
}

/**
 * Build a set of all valid page slugs from modules.json for slug validation.
 */
function getAllValidSlugs(): Set<string> {
  const slugs = new Set<string>();
  for (const module of modulesData as any[]) {
    for (const page of module.pages) {
      slugs.add(page.slug);
    }
  }
  return slugs;
}

/**
 * Find the module containing a given content ID (page.id or slug-based).
 * Returns the module index in modulesData, or -1 if not found.
 */
function findModuleIndexByContentId(contentId: string): number {
  const allModules = modulesData as any[];
  for (let i = 0; i < allModules.length; i++) {
    const module = allModules[i];
    for (const page of module.pages) {
      if (page.id === contentId) return i;
      // Also check slug-based format for backward compatibility
      const contentPath = page.slug.replace('/learn/', '');
      if (contentPath === contentId) return i;
    }
  }
  return -1;
}

/**
 * Get all courses with progress data
 * 
 * @param progress - Progress map from backend (content_id -> completed status)
 * @param lastActiveSlug - Optional slug of the last active lesson from the backend
 * @param mostRecentContentId - Optional content ID of the most recently completed lesson (used for fallback)
 * @returns Array of courses with completion data
 */
export function getAllCourses(
  progress: Record<string, boolean> = {},
  lastActiveSlug?: string,
  mostRecentContentId?: string
): CourseProgress[] {
  const courses: CourseProgress[] = [];

  // Validate lastActiveSlug against modules.json
  const validSlugs = getAllValidSlugs();
  const resolvedLastActiveSlug = lastActiveSlug && validSlugs.has(lastActiveSlug)
    ? lastActiveSlug
    : undefined;

  // modulesData is now an array of all modules
  const allModules = modulesData as any[];

  for (const module of allModules) {
    // Use the learningPath property from the module, not from splitting the ID
    const learningPath = module.learningPath || 'Other';
    const [, topic] = module.id.split('/');
    
    // Calculate total and completed pages
    let totalPages = 0;
    let completedPages = 0;
    let firstIncompleteSlug: string | undefined;

    module.pages.forEach((page: any) => {
      totalPages++;
      // Check completion using both formats for backward compatibility:
      // 1. page.id (new format): e.g., "devsecops-capstone"
      // 2. slug without /learn/ prefix (old format): e.g., "devsecops/capstone/index"
      const contentPath = page.slug.replace('/learn/', '');
      if (progress[page.id] || progress[contentPath]) {
        completedPages++;
      } else if (!firstIncompleteSlug) {
        firstIncompleteSlug = page.slug;
      }
    });

    const percentComplete = totalPages > 0 ? Math.round((completedPages / totalPages) * 100) : 0;
    const firstPageSlug = module.pages[0]?.slug || `/learn/${module.id}`;

    courses.push({
      learningPath,
      topic: topic || module.id,
      title: module.title,
      totalPages,
      completedPages,
      percentComplete,
      firstPageSlug,
      lastActiveSlug: firstIncompleteSlug || firstPageSlug,
      modules: [module]
    });
  }

  // If we have an API-stored last active slug, assign it to the correct course
  if (resolvedLastActiveSlug) {
    const allModules = modulesData as any[];
    let targetIndex = -1;
    for (let i = 0; i < allModules.length; i++) {
      for (const page of allModules[i].pages) {
        if (page.slug === resolvedLastActiveSlug) {
          targetIndex = i;
          break;
        }
      }
      if (targetIndex >= 0) break;
    }
    if (targetIndex >= 0 && courses[targetIndex]) {
      courses[targetIndex].lastActiveSlug = resolvedLastActiveSlug;
    }
  }

  return courses;
}

function formatTitle(slug: string): string {
  return slug
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function getLearningPathTitle(slug: string): string {
  const titles: { [key: string]: string } = {
    'devsecops': 'DevSecOps',
    'DevSecOps': 'DevSecOps',
    'know_before_you_go': 'Know Before You Go',
    'Know Before You Go': 'Know Before You Go',
    'Getting Started': 'Getting Started',
    'cloud_security': 'Cloud Security',
    'application_security': 'Application Security',
    'Walkthroughs': 'Walkthroughs'
  };
  return titles[slug] || formatTitle(slug);
}
