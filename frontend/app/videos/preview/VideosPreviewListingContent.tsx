/**
 * Videos Preview Listing Content (Client Component)
 *
 * Renders the video grid with dynamic data fetching.
 * Imported by the server-side page wrapper which provides SEO metadata.
 */

'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Footer } from '@/components/layout/Footer';
import { Spinner } from '@/components/ui/Spinner';
import { fetchPublicVideos } from '@/lib/video-client';

interface PublicVideo {
  id: string;
  title: string;
  slug: string;
  description: string;
  thumbnailUrl: string | null;
  durationSeconds: number;
  tags: string[];
  instructor: string;
  instructors: Array<{ name: string; linkedinUrl: string | null }>;
  recordedAt: string;
  publishedAt: string | null;
}

function formatDuration(seconds: number): string {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  if (hrs > 0) return `${hrs}h ${mins}m`;
  return `${mins}m`;
}

function VideoPreviewCard({ video }: { video: PublicVideo }) {
  return (
    <Link
      href={`/videos/preview/${video.slug}`}
      className="group bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden hover:border-primary-300 dark:hover:border-primary-700 hover:shadow-lg transition-all flex flex-col"
    >
      {/* Thumbnail */}
      <div className="relative aspect-video bg-gray-100 dark:bg-gray-800">
        {video.thumbnailUrl ? (
          <img
            src={video.thumbnailUrl}
            alt={video.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <svg
              className="w-12 h-12 text-gray-300 dark:text-gray-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
        )}

        {/* Duration badge */}
        <span className="absolute bottom-2 right-2 bg-black/75 text-white text-xs px-2 py-1 rounded">
          {formatDuration(video.durationSeconds)}
        </span>
      </div>

      {/* Content */}
      <div className="p-5 flex flex-col flex-1">
        {/* Badge + Date */}
        <div className="flex items-center gap-2 mb-2">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
            Builder Session
          </span>
          {video.publishedAt && (
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {new Date(video.publishedAt).toLocaleDateString()}
            </span>
          )}
        </div>

        {/* Title */}
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors mb-2 line-clamp-2">
          {video.title}
        </h2>

        {/* Description */}
        {video.description && (
          <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-3 flex-1">
            {video.description}
          </p>
        )}

        {/* Tags */}
        {video.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-auto">
            {video.tags.slice(0, 4).map((tag) => (
              <span
                key={tag}
                className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-xs rounded"
              >
                {tag}
              </span>
            ))}
            {video.tags.length > 4 && (
              <span className="px-2 py-0.5 text-gray-500 dark:text-gray-500 text-xs">
                +{video.tags.length - 4} more
              </span>
            )}
          </div>
        )}
      </div>
    </Link>
  );
}

export function VideosPreviewListingContent() {
  const [videos, setVideos] = useState<PublicVideo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadVideos = async () => {
      setIsLoading(true);
      const { data, error: apiError } = await fetchPublicVideos();
      if (data) {
        setVideos(data.videos);
      } else {
        setError(apiError || 'Failed to load videos');
      }
      setIsLoading(false);
    };

    loadVideos();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <NavbarWithAuth />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
        {/* Header */}
        <div className="mb-10">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-3">
            Builder Session Videos
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-3xl">
            Watch recorded Builder Sessions covering DevSecOps, cloud security,
            and hands-on engineering topics. Learn from real-world projects and
            expert-led deep dives.
          </p>
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Spinner size="lg" />
          </div>
        )}

        {/* Error state */}
        {error && !isLoading && (
          <div className="text-center py-20">
            <p className="text-gray-500 dark:text-gray-400">{error}</p>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !error && videos.length === 0 && (
          <div className="text-center py-20">
            <svg
              className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
              No videos available yet
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Check back soon for new Builder Session recordings.
            </p>
          </div>
        )}

        {/* Video grid */}
        {!isLoading && !error && videos.length > 0 && (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {videos.map((video) => (
              <VideoPreviewCard key={video.id} video={video} />
            ))}
          </div>
        )}

        {/* CTA */}
        <div className="mt-12 bg-primary-50 dark:bg-primary-900/20 rounded-xl border border-primary-200 dark:border-primary-800 p-8 text-center">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Watch the full sessions
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Builder Session videos are available to active Builder tier members.
            Sign up to watch full recordings with progress tracking.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              href="/pricing"
              className="px-6 py-3 bg-yellow-500 hover:bg-yellow-600 text-gray-900 font-semibold rounded-lg transition-colors"
            >
              View Membership Options
            </Link>
            <Link
              href="/login"
              className="px-6 py-3 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-750 rounded-lg font-medium transition-colors"
            >
              Sign In
            </Link>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
