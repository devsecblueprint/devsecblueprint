/**
 * Public Video Preview Page
 *
 * SEO-friendly public page showing video metadata (title, description,
 * tags, duration, instructors). No authentication required — designed for
 * search engine indexing and social sharing.
 */

import { VideoPreviewContent } from './VideoPreviewContent';

// With output: export, we provide a placeholder. Client resolves actual slug.
export function generateStaticParams() {
  return [{ slug: '_' }];
}

export default function VideoPreviewPage() {
  return <VideoPreviewContent />;
}
