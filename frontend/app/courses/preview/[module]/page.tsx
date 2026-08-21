/**
 * Public Module/Course Preview Page
 *
 * SEO-friendly public page showing module metadata (title, learning path,
 * lesson count, lesson titles). No authentication required.
 */

import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { modulesMetadata, getModuleBySlug } from '@/lib/data/modules-metadata';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Footer } from '@/components/layout/Footer';

interface PageProps {
  params: Promise<{ module: string }>;
}

export function generateStaticParams() {
  return modulesMetadata.map((m) => ({ module: m.slug }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { module: slug } = await params;
  const mod = getModuleBySlug(slug);
  if (!mod) return {};

  const title = `${mod.title} — ${mod.learningPath} | Course Preview`;
  const description = `Explore the "${mod.title}" module in the ${mod.learningPath} learning path. ${mod.pageCount} lessons covering key concepts and hands-on exercises.`;

  return {
    title,
    description,
    keywords: [mod.learningPath, mod.title, 'DevSecOps', 'cloud security', 'learning module', 'course preview'],
    openGraph: {
      title,
      description,
      url: `https://devsecblueprint.com/courses/preview/${mod.slug}`,
      siteName: 'The DevSec Blueprint',
      type: 'article',
      images: [
        {
          url: '/og-image.png',
          width: 1200,
          height: 630,
          alt: `${mod.title} — ${mod.learningPath}`,
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
      canonical: `https://devsecblueprint.com/courses/preview/${mod.slug}`,
    },
  };
}

function learningPathColor(path: string): string {
  switch (path) {
    case 'Welcome':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
    case 'Know Before You Go':
      return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400';
    case 'DevSecOps':
      return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400';
    case 'Cloud Security Development':
      return 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-400';
    case 'Career Strategy':
      return 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-400';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
  }
}

export default async function ModulePreviewPage({ params }: PageProps) {
  const { module: slug } = await params;
  const mod = getModuleBySlug(slug);

  if (!mod) {
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
              {mod.title}
            </li>
          </ol>
        </nav>

        {/* Learning Path Badge & Title */}
        <div className="mb-6">
          <div className="flex flex-wrap items-center gap-3 mb-3">
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${learningPathColor(mod.learningPath)}`}
            >
              {mod.learningPath}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {mod.pageCount} {mod.pageCount === 1 ? 'lesson' : 'lessons'}
            </span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100">
            {mod.title}
          </h1>
        </div>

        {/* Description */}
        <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed mb-8">
          This module is part of the <strong>{mod.learningPath}</strong> learning path on The DevSec
          Blueprint. It contains {mod.pageCount} structured lessons designed to build your
          understanding progressively.
        </p>

        {/* Lesson list */}
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 mb-10">
          <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
            Lesson Outline
          </h2>
          <ol className="space-y-3">
            {mod.pageTitles.map((title, index) => (
              <li
                key={index}
                className="flex items-start gap-3 text-gray-700 dark:text-gray-300"
              >
                <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800 text-xs font-medium text-gray-600 dark:text-gray-400">
                  {index + 1}
                </span>
                <span className="text-sm pt-0.5">{title}</span>
              </li>
            ))}
          </ol>
        </div>

        {/* CTA */}
        <div className="bg-primary-50 dark:bg-primary-900/20 rounded-xl border border-primary-200 dark:border-primary-800 p-8 text-center">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Ready to start learning?
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Sign up or log in to access the full lesson content, track your progress, and earn
            completion badges.
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
            name: mod.title,
            description: `${mod.title} module in the ${mod.learningPath} learning path. ${mod.pageCount} lessons.`,
            provider: {
              '@type': 'Organization',
              name: 'The DevSec Blueprint',
              url: 'https://devsecblueprint.com',
            },
            hasCourseInstance: {
              '@type': 'CourseInstance',
              courseMode: 'online',
              courseWorkload: `${mod.pageCount} lessons`,
            },
            isPartOf: {
              '@type': 'Course',
              name: mod.learningPath,
            },
          }),
        }}
      />
    </div>
  );
}
