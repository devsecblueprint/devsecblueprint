/**
 * Public Learning Path Preview Page
 *
 * SEO-friendly public page showing a full learning path overview with all its
 * modules listed. No authentication required.
 */

import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import {
  learningPathsMetadata,
  getLearningPathBySlug,
} from '@/lib/data/learning-paths-metadata';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Footer } from '@/components/layout/Footer';

interface PageProps {
  params: Promise<{ path: string }>;
}

export function generateStaticParams() {
  return learningPathsMetadata.map((lp) => ({ path: lp.slug }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { path: slug } = await params;
  const lp = getLearningPathBySlug(slug);
  if (!lp) return {};

  const title = `${lp.name} Learning Path | The DevSec Blueprint`;
  const description = `Explore the ${lp.name} learning path — ${lp.moduleCount} modules, ${lp.totalLessons} lessons covering hands-on ${lp.name.toLowerCase()} skills from fundamentals to advanced.`;

  return {
    title,
    description,
    keywords: [lp.name, 'learning path', 'DevSecOps', 'cloud security', 'course', 'online learning'],
    openGraph: {
      title,
      description,
      url: `https://devsecblueprint.com/courses/preview/path/${lp.slug}`,
      siteName: 'The DevSec Blueprint',
      type: 'article',
      images: [
        {
          url: '/og-image.png',
          width: 1200,
          height: 630,
          alt: `${lp.name} Learning Path`,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: ['/og-image.png'],
      creator: '@devsecblueprint',
      site: '@devsecblueprint',
    },
    alternates: {
      canonical: `https://devsecblueprint.com/courses/preview/path/${lp.slug}`,
    },
  };
}

function pathColor(name: string): string {
  switch (name) {
    case 'Welcome':
      return 'from-blue-500 to-blue-600';
    case 'Know Before You Go':
      return 'from-purple-500 to-purple-600';
    case 'DevSecOps':
      return 'from-orange-500 to-orange-600';
    case 'Cloud Security Development':
      return 'from-teal-500 to-teal-600';
    case 'Career Strategy':
      return 'from-pink-500 to-pink-600';
    default:
      return 'from-gray-500 to-gray-600';
  }
}

export default async function LearningPathPreviewPage({ params }: PageProps) {
  const { path: slug } = await params;
  const lp = getLearningPathBySlug(slug);

  if (!lp) {
    notFound();
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <NavbarWithAuth />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
        {/* Breadcrumb */}
        <nav className="mb-6 text-sm text-gray-500 dark:text-gray-400" aria-label="Breadcrumb">
          <ol className="flex items-center gap-2">
            <li>
              <Link href="/" className="hover:text-primary-500 transition-colors">
                Home
              </Link>
            </li>
            <li aria-hidden="true">/</li>
            <li>
              <Link href="/courses" className="hover:text-primary-500 transition-colors">
                Courses
              </Link>
            </li>
            <li aria-hidden="true">/</li>
            <li className="text-gray-900 dark:text-gray-100 font-medium" aria-current="page">
              {lp.name}
            </li>
          </ol>
        </nav>

        {/* Hero */}
        <div className="mb-10">
          <div
            className={`inline-flex items-center px-4 py-1.5 rounded-full text-sm font-semibold text-white bg-gradient-to-r ${pathColor(lp.name)} mb-4`}
          >
            Learning Path
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-3">
            {lp.name}
          </h1>
          <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
            A structured learning path with {lp.moduleCount} modules and {lp.totalLessons} lessons.
            Progress from foundational concepts to hands-on application.
          </p>
          <div className="flex items-center gap-4 mt-4 text-sm text-gray-500 dark:text-gray-400">
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              {lp.moduleCount} modules
            </span>
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              {lp.totalLessons} lessons
            </span>
          </div>
        </div>

        {/* Module list */}
        <div className="space-y-4 mb-10">
          <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            Modules in this path
          </h2>
          {lp.modules.map((mod, index) => (
            <Link
              key={mod.previewSlug}
              href={`/courses/preview/${mod.previewSlug}`}
              className="block bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 hover:border-primary-300 dark:hover:border-primary-700 hover:shadow-sm transition-all group"
            >
              <div className="flex items-start gap-4">
                <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg bg-gray-100 dark:bg-gray-800 text-sm font-semibold text-gray-600 dark:text-gray-400 group-hover:bg-primary-100 dark:group-hover:bg-primary-900/30 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                  {index + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                    {mod.title}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                    {mod.pageCount} {mod.pageCount === 1 ? 'lesson' : 'lessons'}
                  </p>
                </div>
                <svg
                  className="w-5 h-5 text-gray-400 group-hover:text-primary-500 transition-colors flex-shrink-0 mt-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </Link>
          ))}
        </div>

        {/* CTA */}
        <div className="bg-primary-50 dark:bg-primary-900/20 rounded-xl border border-primary-200 dark:border-primary-800 p-8 text-center">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Start the {lp.name} path
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Sign up to access all lessons, track your progress through each module, and earn your
            completion badge.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              href="/login"
              className="px-6 py-3 bg-primary-500 hover:bg-primary-600 text-white rounded-lg font-medium transition-colors"
            >
              Get Started
            </Link>
            <Link
              href="/pricing"
              className="px-6 py-3 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-750 rounded-lg font-medium transition-colors"
            >
              View Plans
            </Link>
          </div>
        </div>
      </main>

      <Footer />

      {/* Structured data for SEO */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'Course',
            name: `${lp.name} Learning Path`,
            description: `Structured learning path with ${lp.moduleCount} modules and ${lp.totalLessons} lessons.`,
            provider: {
              '@type': 'Organization',
              name: 'The DevSec Blueprint',
              url: 'https://devsecblueprint.com',
            },
            hasCourseInstance: {
              '@type': 'CourseInstance',
              courseMode: 'online',
              courseWorkload: `${lp.moduleCount} modules, ${lp.totalLessons} lessons`,
            },
            numberOfCredits: lp.moduleCount,
            hasPart: lp.modules.map((mod) => ({
              '@type': 'Course',
              name: mod.title,
              url: `https://devsecblueprint.com/courses/preview/${mod.previewSlug}`,
            })),
          }),
        }}
      />
    </div>
  );
}
