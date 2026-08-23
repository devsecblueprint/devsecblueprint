/**
 * Video Preview Content (Client Component)
 *
 * Public-facing preview page for a video. Shows metadata without
 * requiring authentication. Encourages sign-up/membership for playback.
 */

'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Spinner } from '@/components/ui/Spinner';
import { Card } from '@/components/ui/Card';
import { fetchPublicVideo } from '@/lib/video-client';
import type { PublicVideoItem } from '@/lib/video-client';

function formatDuration(seconds: number): string {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  if (hrs > 0) return `${hrs}h ${mins}m`;
  return `${mins}m`;
}

export function VideoPreviewContent() {
  const [slug, setSlug] = useState<string>('');
  const [video, setVideo] = useState<PublicVideoItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const path = window.location.pathname;
    const segments = path.split('/').filter(Boolean);
    // /videos/preview/{slug}
    if (segments.length >= 3 && segments[1] === 'preview') {
      setSlug(segments[2]);
    }
  }, []);

  useEffect(() => {
    if (!slug) return;

    const loadVideo = async () => {
      setIsLoading(true);
      const { data, error: apiError } = await fetchPublicVideo(slug);
      if (data) {
        setVideo(data);
      } else {
        setError(apiError || 'Video not found');
      }
      setIsLoading(false);
    };

    loadVideo();
  }, [slug]);

  if (!slug || isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
        <NavbarWithAuth />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
          <div className="flex items-center justify-center py-20">
            <Spinner size="lg" />
          </div>
        </main>
      </div>
    );
  }

  if (error || !video) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
        <NavbarWithAuth />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
          <div className="text-center py-20">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              Video Not Found
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              This video may not be available yet or the URL is incorrect.
            </p>
            <Link
              href="/videos"
              className="text-primary-500 hover:text-primary-600 font-medium"
            >
              Browse All Videos
            </Link>
          </div>
        </main>
      </div>
    );
  }

  const instructorDisplay =
    video.instructors && video.instructors.length > 0
      ? video.instructors
      : [{ name: video.instructor || 'DSB Team', linkedinUrl: null }];

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
              <Link href="/videos/preview" className="hover:text-primary-500 transition-colors">
                Videos
              </Link>
            </li>
            <li aria-hidden="true">/</li>
            <li className="text-gray-900 dark:text-gray-100 font-medium" aria-current="page">
              {video.title}
            </li>
          </ol>
        </nav>

        {/* Title & Duration */}
        <div className="mb-6">
          <div className="flex flex-wrap items-center gap-3 mb-3">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
              Builder Session
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {formatDuration(video.durationSeconds)}
            </span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100">
            {video.title}
          </h1>
        </div>

        {/* Description */}
        {video.description && (
          <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed mb-8">
            {video.description}
          </p>
        )}

        {/* Metadata cards */}
        <div className="grid gap-6 sm:grid-cols-2 mb-10">
          {/* Tags/Topics */}
          {video.tags.length > 0 && (
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
              <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                Topics Covered
              </h2>
              <div className="flex flex-wrap gap-2">
                {video.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-3 py-1 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 text-sm rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Instructors */}
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
            <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
              {instructorDisplay.length > 1 ? 'Instructors' : 'Instructor'}
            </h2>
            <ul className="space-y-2">
              {instructorDisplay.map((inst, idx) => (
                <li key={idx} className="flex items-center gap-2">
                  <span className="text-sm text-gray-900 dark:text-gray-100 font-medium">
                    {inst.name}
                  </span>
                  {inst.linkedinUrl && (
                    <a
                      href={inst.linkedinUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 dark:text-blue-400 hover:text-blue-700"
                      aria-label={`${inst.name} on LinkedIn`}
                    >
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                      </svg>
                    </a>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Video details */}
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 mb-10">
          <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
            Video Details
          </h2>
          <dl className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
            <div>
              <dt className="text-gray-500 dark:text-gray-400">Duration</dt>
              <dd className="font-medium text-gray-900 dark:text-gray-100">
                {formatDuration(video.durationSeconds)}
              </dd>
            </div>
            <div>
              <dt className="text-gray-500 dark:text-gray-400">Recorded</dt>
              <dd className="font-medium text-gray-900 dark:text-gray-100">
                {new Date(video.recordedAt).toLocaleDateString()}
              </dd>
            </div>
            {video.publishedAt && (
              <div>
                <dt className="text-gray-500 dark:text-gray-400">Published</dt>
                <dd className="font-medium text-gray-900 dark:text-gray-100">
                  {new Date(video.publishedAt).toLocaleDateString()}
                </dd>
              </div>
            )}
            <div>
              <dt className="text-gray-500 dark:text-gray-400">Topics</dt>
              <dd className="font-medium text-gray-900 dark:text-gray-100">
                {video.tags.length}
              </dd>
            </div>
          </dl>
        </div>

        {/* CTA */}
        <Card className="text-center">
          <div className="py-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-3">
              Watch This Video
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
              Builder Session Videos are available to active Builder tier members.
              Sign up or upgrade your membership to watch the full video.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link
                href="/pricing"
                className="px-6 py-3 bg-yellow-500 hover:bg-yellow-600 text-gray-900 font-semibold rounded-lg transition-colors"
              >
                View Membership Options
              </Link>
              <Link
                href="/login"
                className="px-6 py-3 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                Sign In
              </Link>
            </div>
          </div>
        </Card>
      </main>
    </div>
  );
}
