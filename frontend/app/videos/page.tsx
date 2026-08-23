/**
 * Videos Catalog Page
 *
 * Displays the member videos catalog with search, filters,
 * Continue Watching, Latest Videos, and All Published sections.
 * Protected by AuthGuard + entitlement check.
 *
 * Requirements: 9.1-9.10, 11.1-11.7
 */

'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { AuthGuard } from '@/components/AuthGuard';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Spinner } from '@/components/ui/Spinner';
import { Card } from '@/components/ui/Card';
import { useAuth } from '@/lib/hooks/useAuth';
import { useVideos } from '@/lib/hooks/useVideos';
import { RestrictedAccess } from './components/RestrictedAccess';
import type { CatalogVideoItem, VideoFilters } from '@/lib/video-types';

function formatDuration(seconds: number): string {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  if (hrs > 0) return `${hrs}h ${mins}m`;
  return `${mins}m`;
}

function VideoCard({ video }: { video: CatalogVideoItem }) {
  return (
    <Link href={`/videos/${video.slug}`}>
      <Card className="hover:shadow-xl transition-shadow duration-200 h-full">
        {/* Thumbnail */}
        <div className="relative aspect-video bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden mb-4">
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

          {/* Progress bar */}
          {video.progressPercent > 0 && (
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-300/50">
              <div
                className="h-full bg-yellow-500"
                style={{ width: `${video.progressPercent}%` }}
              />
            </div>
          )}
        </div>

        {/* Title */}
        <h3 className="font-semibold text-gray-900 dark:text-gray-100 line-clamp-2 mb-2">
          {video.title}
        </h3>

        {/* Tags */}
        {video.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2">
            {video.tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Published date */}
        <p className="text-sm text-gray-500 dark:text-gray-500">
          {new Date(video.publishedAt).toLocaleDateString()}
        </p>
      </Card>
    </Link>
  );
}

function VideosSection({
  title,
  videos,
  emptyMessage,
}: {
  title: string;
  videos: CatalogVideoItem[];
  emptyMessage?: string;
}) {
  if (videos.length === 0 && !emptyMessage) return null;

  return (
    <section className="mb-10">
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
        {title}
      </h2>
      {videos.length === 0 ? (
        <p className="text-gray-500 dark:text-gray-400">{emptyMessage}</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {videos.map((rec) => (
            <VideoCard key={rec.id} video={rec} />
          ))}
        </div>
      )}
    </section>
  );
}

function CatalogContent() {
  const [filters, setFilters] = useState<VideoFilters>({ page: 1, pageSize: 20 });
  const [search, setSearch] = useState('');
  const { catalog, isLoading, error } = useVideos(filters);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setFilters((prev) => ({ ...prev, search, page: 1 }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    // Check if it's a 403 (entitlement failure)
    if (error.includes('403') || error.includes('entitlement')) {
      return <RestrictedAccess />;
    }
    return (
      <div className="text-center py-20">
        <p className="text-red-500 dark:text-red-400">{error}</p>
      </div>
    );
  }

  if (!catalog) return null;

  return (
    <div>
      {/* Search bar */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex gap-3">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search videos..."
            className="flex-1 px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-yellow-500"
          />
          <button
            type="submit"
            className="px-6 py-3 bg-yellow-500 hover:bg-yellow-600 text-gray-900 font-semibold rounded-lg transition-colors"
          >
            Search
          </button>
        </div>
      </form>

      {/* Continue Watching */}
      <VideosSection
        title="Continue Watching"
        videos={catalog.continueWatching}
      />

      {/* Latest Videos */}
      <VideosSection
        title="Latest Videos"
        videos={catalog.latest}
      />

      {/* All Published */}
      <VideosSection
        title="All Videos"
        videos={catalog.allPublished}
        emptyMessage="No videos available yet."
      />

      {/* Pagination */}
      {catalog.totalCount > catalog.pageSize && (
        <div className="flex items-center justify-center gap-4 mt-8">
          <button
            onClick={() =>
              setFilters((prev) => ({
                ...prev,
                page: Math.max(1, (prev.page || 1) - 1),
              }))
            }
            disabled={catalog.page <= 1}
            className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Page {catalog.page} of{' '}
            {Math.ceil(catalog.totalCount / catalog.pageSize)}
          </span>
          <button
            onClick={() =>
              setFilters((prev) => ({
                ...prev,
                page: (prev.page || 1) + 1,
              }))
            }
            disabled={
              catalog.page >= Math.ceil(catalog.totalCount / catalog.pageSize)
            }
            className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

export default function VideosPage() {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
        <NavbarWithAuth />

        <main className="pt-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                Builder Session Videos
              </h1>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Watch recorded Builder Sessions and track your learning progress.
              </p>
            </div>

            <CatalogContent />
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
