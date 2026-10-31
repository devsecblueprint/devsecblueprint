/**
 * Public Video Library Preview Listing Page
 *
 * SEO-friendly public page showing all published Video Library videos.
 * Links to individual video preview pages. No authentication required —
 * designed for search engine indexing and social sharing.
 */

import type { Metadata } from 'next';
import { VideosPreviewListingContent } from './VideosPreviewListingContent';

const DESCRIPTION =
  'Watch on-demand Builder Session recordings and workshops covering DevSecOps, cloud security, and hands-on engineering topics. Some videos are free with an account.';

export const metadata: Metadata = {
  title: 'Video Library | The DevSec Blueprint',
  description: DESCRIPTION,
  keywords: [
    'DevSecOps videos',
    'cloud security recordings',
    'DevSecOps workshops',
    'builder sessions',
    'security engineering',
    'hands-on security',
    'DevSec Blueprint',
  ],
  openGraph: {
    title: 'Video Library | The DevSec Blueprint',
    description: DESCRIPTION,
    url: 'https://devsecblueprint.com/videos/preview',
    siteName: 'The DevSec Blueprint',
    type: 'website',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'The DevSec Blueprint — Video Library',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Video Library | The DevSec Blueprint',
    description: DESCRIPTION,
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
