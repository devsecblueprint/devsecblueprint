/**
 * Public Walkthrough Preview Page
 *
 * SEO-friendly public page showing walkthrough metadata (title, description,
 * difficulty, topics, prerequisites, estimated time, authors).
 * No authentication required — designed for search engine indexing.
 */

import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { WALKTHROUGHS_DATA } from '@/lib/walkthroughs-data';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Footer } from '@/components/layout/Footer';

interface PageProps {
  params: Promise<{ slug: string }>;
}

export function generateStaticParams() {
  return WALKTHROUGHS_DATA.map((w) => ({ slug: w.id }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const walkthrough = WALKTHROUGHS_DATA.find((w) => w.id === slug);
  if (!walkthrough) return {};

  const title = `${walkthrough.title} — Walkthrough Preview`;
  const description = walkthrough.description;

  return {
    title,
    description,
    keywords: [...walkthrough.topics, 'walkthrough', 'hands-on', 'DevSecOps', 'cloud security'],
    openGraph: {
      title,
      description,
      url: `https://devsecblueprint.com/walkthroughs/preview/${walkthrough.id}`,
      siteName: 'The DevSec Blueprint',
      type: 'article',
      images: [
        {
          url: '/og-image.png',
          width: 1200,
          height: 630,
          alt: walkthrough.title,
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
      canonical: `https://devsecblueprint.com/walkthroughs/preview/${walkthrough.id}`,
    },
  };
}

function formatTime(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const remaining = minutes % 60;
  return remaining > 0 ? `${hours}h ${remaining}m` : `${hours}h`;
}

function difficultyColor(difficulty: string): string {
  switch (difficulty) {
    case 'Beginner':
      return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
    case 'Intermediate':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
    case 'Advanced':
      return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
  }
}

export default async function WalkthroughPreviewPage({ params }: PageProps) {
  const { slug } = await params;
  const walkthrough = WALKTHROUGHS_DATA.find((w) => w.id === slug);

  if (!walkthrough) {
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
              {walkthrough.title}
            </li>
          </ol>
        </nav>

        {/* Title & Difficulty Badge */}
        <div className="mb-6">
          <div className="flex flex-wrap items-center gap-3 mb-3">
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${difficultyColor(walkthrough.difficulty)}`}
            >
              {walkthrough.difficulty}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {formatTime(walkthrough.estimatedTime)} estimated
            </span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100">
            {walkthrough.title}
          </h1>
        </div>

        {/* Description */}
        <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed mb-8">
          {walkthrough.description}
        </p>

        {/* Metadata cards */}
        <div className="grid gap-6 sm:grid-cols-2 mb-10">
          {/* Topics */}
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
            <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
              Topics Covered
            </h2>
            <div className="flex flex-wrap gap-2">
              {walkthrough.topics.map((topic) => (
                <span
                  key={topic}
                  className="px-3 py-1 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 text-sm rounded-full"
                >
                  {topic}
                </span>
              ))}
            </div>
          </div>

          {/* Prerequisites */}
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
            <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
              Prerequisites
            </h2>
            <ul className="space-y-2">
              {walkthrough.prerequisites.map((prereq) => (
                <li
                  key={prereq}
                  className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300"
                >
                  <svg
                    className="w-4 h-4 mt-0.5 text-gray-400 dark:text-gray-500 flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4"
                    />
                  </svg>
                  {prereq}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Authors */}
        {walkthrough.authors && walkthrough.authors.length > 0 && (
          <div className="mb-10">
            <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
              Created by
            </h2>
            <div className="flex flex-wrap gap-4">
              {walkthrough.authors.map((author) => (
                <span key={author.name} className="text-gray-900 dark:text-gray-100 font-medium">
                  {author.url ? (
                    <a
                      href={author.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-primary-500 transition-colors"
                    >
                      {author.name}
                    </a>
                  ) : (
                    author.name
                  )}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Repository link */}
        {walkthrough.repositoryUrl && (
          <div className="mb-10">
            <a
              href={walkthrough.repositoryUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path
                  fillRule="evenodd"
                  d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                  clipRule="evenodd"
                />
              </svg>
              View Source Repository
            </a>
          </div>
        )}

        {/* CTA */}
        <div className="bg-primary-50 dark:bg-primary-900/20 rounded-xl border border-primary-200 dark:border-primary-800 p-8 text-center">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Ready to get started?
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Sign up or log in to access the full walkthrough with step-by-step instructions and progress tracking.
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
            name: walkthrough.title,
            description: walkthrough.description,
            provider: {
              '@type': 'Organization',
              name: 'The DevSec Blueprint',
              url: 'https://devsecblueprint.com',
            },
            educationalLevel: walkthrough.difficulty,
            timeRequired: `PT${walkthrough.estimatedTime}M`,
            teaches: walkthrough.topics.join(', '),
            ...(walkthrough.authors?.[0] && {
              creator: {
                '@type': 'Person',
                name: walkthrough.authors[0].name,
                ...(walkthrough.authors[0].url && { url: walkthrough.authors[0].url }),
              },
            }),
          }),
        }}
      />
    </div>
  );
}
