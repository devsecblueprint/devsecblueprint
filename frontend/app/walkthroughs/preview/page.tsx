/**
 * Public Walkthroughs Preview Listing Page
 *
 * SEO-friendly public page showing all available walkthroughs.
 * Links to individual walkthrough preview pages. No authentication required.
 */

import type { Metadata } from 'next';
import Link from 'next/link';
import { WALKTHROUGHS_DATA } from '@/lib/walkthroughs-data';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Footer } from '@/components/layout/Footer';

export const metadata: Metadata = {
  title: 'Hands-On Walkthroughs | The DevSec Blueprint',
  description:
    'Explore hands-on DevSecOps and cloud security walkthroughs. Build real pipelines, security controls, and home labs with step-by-step guidance.',
  keywords: [
    'DevSecOps walkthroughs',
    'cloud security labs',
    'hands-on security',
    'CI/CD pipeline tutorial',
    'AWS security',
    'Azure security',
    'GCP security',
  ],
  openGraph: {
    title: 'Hands-On Walkthroughs | The DevSec Blueprint',
    description:
      'Explore hands-on DevSecOps and cloud security walkthroughs. Build real pipelines, security controls, and home labs.',
    url: 'https://devsecblueprint.com/walkthroughs/preview',
    siteName: 'The DevSec Blueprint',
    type: 'website',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'The DevSec Blueprint — Hands-On Walkthroughs',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Hands-On Walkthroughs | The DevSec Blueprint',
    description:
      'Explore hands-on DevSecOps and cloud security walkthroughs. Build real pipelines, security controls, and home labs.',
    images: ['/og-image.png'],
    creator: '@devsecblueprint',
    site: '@devsecblueprint',
  },
  alternates: {
    canonical: 'https://devsecblueprint.com/walkthroughs/preview',
  },
};

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

export default function WalkthroughsPreviewListingPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <NavbarWithAuth />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
        {/* Header */}
        <div className="mb-10">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-3">
            Hands-On Walkthroughs
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-3xl">
            Build real-world DevSecOps pipelines, security controls, and home labs. Each
            walkthrough includes step-by-step instructions, architecture diagrams, and source code.
          </p>
        </div>

        {/* Walkthrough grid */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {WALKTHROUGHS_DATA.map((walkthrough) => (
            <Link
              key={walkthrough.id}
              href={`/walkthroughs/preview/${walkthrough.id}`}
              className="group bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 hover:border-primary-300 dark:hover:border-primary-700 hover:shadow-lg transition-all flex flex-col"
            >
              {/* Difficulty + Time */}
              <div className="flex items-center gap-2 mb-3">
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${difficultyColor(walkthrough.difficulty)}`}
                >
                  {walkthrough.difficulty}
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {formatTime(walkthrough.estimatedTime)}
                </span>
              </div>

              {/* Title */}
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors mb-2">
                {walkthrough.title}
              </h2>

              {/* Description */}
              <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3 mb-4 flex-1">
                {walkthrough.description}
              </p>

              {/* Topics */}
              <div className="flex flex-wrap gap-1.5 mt-auto">
                {walkthrough.topics.slice(0, 4).map((topic) => (
                  <span
                    key={topic}
                    className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-xs rounded"
                  >
                    {topic}
                  </span>
                ))}
                {walkthrough.topics.length > 4 && (
                  <span className="px-2 py-0.5 text-gray-500 dark:text-gray-500 text-xs">
                    +{walkthrough.topics.length - 4} more
                  </span>
                )}
              </div>
            </Link>
          ))}
        </div>

        {/* CTA */}
        <div className="mt-12 bg-primary-50 dark:bg-primary-900/20 rounded-xl border border-primary-200 dark:border-primary-800 p-8 text-center">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Ready to build?
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Sign up to access full walkthrough content with progress tracking and community support.
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

      {/* Structured data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'CollectionPage',
            name: 'Hands-On DevSecOps Walkthroughs',
            description:
              'A collection of hands-on walkthroughs covering DevSecOps pipelines, cloud security controls, and home labs.',
            provider: {
              '@type': 'Organization',
              name: 'The DevSec Blueprint',
              url: 'https://devsecblueprint.com',
            },
            hasPart: WALKTHROUGHS_DATA.map((w) => ({
              '@type': 'Course',
              name: w.title,
              url: `https://devsecblueprint.com/walkthroughs/preview/${w.id}`,
            })),
          }),
        }}
      />
    </div>
  );
}
