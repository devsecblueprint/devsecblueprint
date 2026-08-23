/**
 * Public Videos Preview Listing Page
 *
 * SEO-friendly public page showing all published Builder Session videos.
 * Links to individual video preview pages. No authentication required —
 * designed for search engine indexing and social sharing.
 */

import type { Metadata } from 'next';
import { VideosPreviewListingContent } from './VideosPreviewListingContent';

export const metadata: Metadata = {
  title: 'Builder Session Videos | The DevSec Blueprint',
  description:
    'Watch recorded Builder Sessions covering DevSecOps, cloud security, and hands-on engineering topics. Learn from real-world projects and expert-led deep dives.',
  keywords: [
    'DevSecOps videos',
    'cloud security recordings',
    'builder sessions',
    'security engineering',
    'hands-on security',
    'DevSec Blueprint',
  ],
  openGraph: {
    title: 'Builder Session Videos | The DevSec Blueprint',
    description:
      'Watch recorded Builder Sessions covering DevSecOps, cloud security, and hands-on engineering topics.',
    url: 'https://devsecblueprint.com/videos/preview',
    siteName: 'The DevSec Blueprint',
    type: 'website',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'The DevSec Blueprint — Builder Session Videos',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Builder Session Videos | The DevSec Blueprint',
    description:
      'Watch recorded Builder Sessions covering DevSecOps, cloud security, and hands-on engineering topics.',
    images: ['/og-image.png'],
    creator: '@devsecblueprint',
    site: '@devsecblueprint',
  },
  alternates: {
    canonical: 'https://devsecblueprint.com/videos/preview',
  },
};

export default function VideosPreviewPage() {
  return <VideosPreviewListingContent />;
}
