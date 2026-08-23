/**
 * Individual Video Page (Server wrapper)
 *
 * Provides generateStaticParams for static export compatibility.
 * All rendering is delegated to the client VideoPageContent component.
 *
 * Requirements: 10.1-10.15
 */

import { VideoPageContent } from './VideoPageContent';

// With output: export, all dynamic route params must be enumerated.
// We provide a single catch-all placeholder — the client component
// uses useParams() to resolve the actual slug at runtime.
export function generateStaticParams() {
  return [{ slug: '_' }];
}

export default function VideoPage() {
  return <VideoPageContent />;
}
