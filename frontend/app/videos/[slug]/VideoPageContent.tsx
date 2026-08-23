/**
 * Individual Video Page Content (Client Component)
 *
 * Displays a single video with Cloudflare Stream player,
 * metadata, tabbed content (Overview, Resources, Instructor),
 * progress tracking, and a right sidebar.
 *
 * Requirements: 10.1-10.15
 */

'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { AuthGuard } from '@/components/AuthGuard';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Spinner } from '@/components/ui/Spinner';
import { Card } from '@/components/ui/Card';
import { useVideo } from '@/lib/hooks/useVideos';
import {
  usePlaybackProgress,
  usePlaybackToken,
} from '@/lib/hooks/usePlaybackProgress';
import { RestrictedAccess } from '../components/RestrictedAccess';

type Tab = 'overview' | 'resources' | 'instructor';

function formatDuration(seconds: number): string {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  if (hrs > 0) return `${hrs}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  return `${mins}:${String(secs).padStart(2, '0')}`;
}

function VideoContent() {
  const [slug, setSlug] = useState<string>('');
  const { video, isLoading, error } = useVideo(slug);
  const [activeTab, setActiveTab] = useState<Tab>('overview');

  // Read slug from the actual browser URL, not useParams
  // (useParams returns the static placeholder '_' with output: export)
  useEffect(() => {
    const path = window.location.pathname;
    const segments = path.split('/').filter(Boolean);
    // /videos/{slug} -> segments = ['videos', '{slug}']
    if (segments.length >= 2 && segments[0] === 'videos') {
      setSlug(segments[1]);
    }
  }, []);

  if (!slug) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    if (error.includes('403') || error.includes('entitlement')) {
      return <RestrictedAccess />;
    }
    return (
      <div className="text-center py-20">
        <p className="text-red-500 dark:text-red-400">{error}</p>
      </div>
    );
  }

  if (!video) return null;

  return (
    <div>
      {/* Breadcrumb */}
      <nav className="mb-6" aria-label="Breadcrumb">
        <Link
          href="/videos"
          className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
        >
          &larr; Back to Videos
        </Link>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main content area */}
        <div className="lg:col-span-2">
          {/* Player */}
          <PlayerSection
            recordingId={video.id}
            durationSeconds={video.durationSeconds}
          />

          {/* Title and metadata */}
          <div className="mt-6">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {video.title}
            </h1>
            <div className="flex flex-wrap items-center gap-4 mt-3 text-sm text-gray-500 dark:text-gray-400">
              <span>{video.instructor}</span>
              <span>&middot;</span>
              <span>{new Date(video.recordedAt).toLocaleDateString()}</span>
              <span>&middot;</span>
              <span>{formatDuration(video.durationSeconds)}</span>
            </div>

            {/* Tags */}
            {video.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-4">
                {video.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs px-3 py-1 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Tabs */}
          <div className="mt-8 border-b border-gray-200 dark:border-gray-800">
            <nav className="flex gap-6">
              {(['overview', 'resources', 'instructor'] as Tab[]).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`pb-3 text-sm font-medium capitalize transition-colors ${
                    activeTab === tab
                      ? 'text-yellow-600 dark:text-yellow-400 border-b-2 border-yellow-500'
                      : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab content */}
          <div className="mt-6">
            {activeTab === 'overview' && (
              <div className="prose dark:prose-invert max-w-none">
                <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {video.description || 'No description available.'}
                </p>
              </div>
            )}

            {activeTab === 'resources' && (
              <div>
                {video.resources.length === 0 ? (
                  <p className="text-gray-500 dark:text-gray-400">
                    No resources available for this video.
                  </p>
                ) : (
                  <ul className="space-y-3">
                    {video.resources.map((resource, idx) => (
                      <li key={idx}>
                        <a
                          href={resource.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                        >
                          <svg
                            className="w-5 h-5 text-gray-400 flex-shrink-0"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                            />
                          </svg>
                          <span className="text-gray-900 dark:text-gray-100">
                            {resource.title}
                          </span>
                        </a>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {activeTab === 'instructor' && (
              <div>
                {video.instructors && video.instructors.length > 0 ? (
                  <ul className="space-y-3">
                    {video.instructors.map((inst, idx) => (
                      <li key={idx} className="flex items-center gap-3">
                        <span className="font-medium text-gray-900 dark:text-gray-100">
                          {inst.name}
                        </span>
                        {inst.linkedinUrl && (
                          <a
                            href={inst.linkedinUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700"
                          >
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                            </svg>
                            LinkedIn
                          </a>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-700 dark:text-gray-300">
                    <span className="font-semibold">Instructor:</span>{' '}
                    {video.instructor}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right sidebar */}
        <aside className="lg:col-span-1">
          <Card className="sticky top-24">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Video Info
            </h3>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-gray-500 dark:text-gray-400">Duration</dt>
                <dd className="text-gray-900 dark:text-gray-100 font-medium">
                  {formatDuration(video.durationSeconds)}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500 dark:text-gray-400">Recorded</dt>
                <dd className="text-gray-900 dark:text-gray-100 font-medium">
                  {new Date(video.recordedAt).toLocaleDateString()}
                </dd>
              </div>
              {video.publishedAt && (
                <div>
                  <dt className="text-gray-500 dark:text-gray-400">Published</dt>
                  <dd className="text-gray-900 dark:text-gray-100 font-medium">
                    {new Date(video.publishedAt).toLocaleDateString()}
                  </dd>
                </div>
              )}
              <div>
                <dt className="text-gray-500 dark:text-gray-400">Instructor</dt>
                <dd className="text-gray-900 dark:text-gray-100 font-medium">
                  {video.instructor}
                </dd>
              </div>
            </dl>
          </Card>
        </aside>
      </div>
    </div>
  );
}

function PlayerSection({
  recordingId,
  durationSeconds,
}: {
  recordingId: string;
  durationSeconds: number;
}) {
  const { token, isLoading: tokenLoading, error: tokenError } = usePlaybackToken(recordingId);
  const { progress } = usePlaybackProgress(recordingId);

  if (tokenLoading) {
    return (
      <div className="aspect-video bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (tokenError || !token) {
    return (
      <div className="aspect-video bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
        <p className="text-gray-500 dark:text-gray-400">
          {tokenError || 'Unable to load video player'}
        </p>
      </div>
    );
  }

  const playerSrc = `https://iframe.videodelivery.net/${token}?preload=metadata${
    progress?.positionSeconds ? `&startTime=${progress.positionSeconds}` : ''
  }`;

  return (
    <div className="aspect-video bg-black rounded-lg overflow-hidden">
      <iframe
        src={playerSrc}
        className="w-full h-full"
        allow="accelerometer; gyroscope; autoplay; encrypted-media; picture-in-picture"
        allowFullScreen
        title="Video player"
      />
    </div>
  );
}

export function VideoPageContent() {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
        <NavbarWithAuth />

        <main className="pt-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <VideoContent />
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
