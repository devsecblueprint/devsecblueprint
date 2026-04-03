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
 * Get all courses with progress data
 * 
 * @param progress - Progress map from backend (content_id -> completed status)
 * @param lastActiveSlug - Optional slug of the last active lesson from the backend
 * @returns Array of courses with completion data
 */
export function getAllCourses(
  progress: Record<string, boolean> = {},
  lastActiveSlug?: string
): CourseProgress[] {
  const courses: CourseProgress[] = [];

  // Validate lastActiveSlug against modules.json
  const validSlugs = getAllValidSlugs();
  const resolvedLastActiveSlug = lastActiveSlug && validSlugs.has(lastActiveSlug)
    ? lastActiveSlug
    : undefined;

  // modulesData is now an array of all modules
  const allModules = modulesData as any[];
  let lastActiveSlugAssigned = false;

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

    // Resolve lastActiveSlug for the first incomplete course
    let courseLastActiveSlug: string;
    if (!lastActiveSlugAssigned && percentComplete < 100) {
      courseLastActiveSlug = resolvedLastActiveSlug || firstIncompleteSlug || firstPageSlug;
      lastActiveSlugAssigned = true;
    } else {
      courseLastActiveSlug = firstIncompleteSlug || firstPageSlug;
    }

    courses.push({
      learningPath,
      topic: topic || module.id,
      title: module.title,
      totalPages,
      completedPages,
      percentComplete,
      firstPageSlug,
      lastActiveSlug: courseLastActiveSlug,
      modules: [module]
    });
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
