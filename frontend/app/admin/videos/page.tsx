/**
 * Admin Video Management Page
 *
 * Allows admins to manage videos: view, create, edit, and
 * transition video status. Includes status filter tabs,
 * a data table, and an Add Video modal.
 *
 * Requirements: 12.1-12.11
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { AuthGuard } from '@/components/AuthGuard';
import { useAuth } from '@/lib/hooks/useAuth';
import { Card } from '@/components/ui/Card';
import { Spinner } from '@/components/ui/Spinner';
import {
  adminListVideos,
  adminCreateVideo,
  adminUpdateVideo,
  adminTransitionStatus,
} from '@/lib/video-client';
import type {
  Video,
  VideoStatus,
  CreateVideoRequest,
  UpdateVideoRequest,
} from '@/lib/video-types';

const STATUS_TABS: { label: string; value: VideoStatus | 'ALL' }[] = [
  { label: 'All', value: 'ALL' },
  { label: 'Draft', value: 'DRAFT' },
  { label: 'Processing', value: 'PROCESSING' },
  { label: 'Ready', value: 'READY' },
  { label: 'Published', value: 'PUBLISHED' },
  { label: 'Archived', value: 'ARCHIVED' },
];

const STATUS_COLORS: Record<VideoStatus, string> = {
  DRAFT: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
  PROCESSING: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  READY: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  PUBLISHED: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
  ARCHIVED: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
};

function formatDuration(seconds: number): string {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  if (hrs > 0) return `${hrs}h ${mins}m`;
  return `${mins}m`;
}

function AddVideoModal({
  isOpen,
  onClose,
  onCreated,
}: {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [title, setTitle] = useState('');
  const [instructor, setInstructor] = useState('');
  const [cloudflareStreamId, setCloudflareStreamId] = useState('');
  const [recordedAt, setRecordedAt] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const data: CreateVideoRequest = {
      title,
      instructor,
      cloudflareStreamId,
      recordedAt,
      description,
    };

    const { data: result, error: apiError } = await adminCreateVideo(data);

    if (result) {
      onCreated();
      onClose();
      setTitle('');
      setInstructor('');
      setCloudflareStreamId('');
      setRecordedAt('');
      setDescription('');
    } else {
      setError(apiError || 'Failed to create video');
    }

    setIsSubmitting(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="relative bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-lg w-full mx-4 p-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-6">
          Add Video
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              maxLength={200}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-yellow-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Instructor *
            </label>
            <input
              type="text"
              value={instructor}
              onChange={(e) => setInstructor(e.target.value)}
              required
              maxLength={200}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-yellow-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Cloudflare Stream ID *
            </label>
            <input
              type="text"
              value={cloudflareStreamId}
              onChange={(e) => setCloudflareStreamId(e.target.value)}
              required
              maxLength={64}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-yellow-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Recorded At *
            </label>
            <input
              type="date"
              value={recordedAt}
              onChange={(e) => setRecordedAt(e.target.value)}
              required
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-yellow-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={5000}
              rows={3}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-yellow-500"
            />
          </div>

          {error && (
            <p className="text-sm text-red-500 dark:text-red-400">{error}</p>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-gray-900 font-semibold rounded-lg transition-colors disabled:opacity-50"
            >
              {isSubmitting ? 'Creating...' : 'Create Video'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function EditVideoModal({
  video,
  onClose,
  onSaved,
}: {
  video: Video;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [title, setTitle] = useState(video.title);
  const [instructorEntries, setInstructorEntries] = useState<
    Array<{ name: string; linkedinUrl: string }>
  >(() => {
    if (video.instructors && video.instructors.length > 0) {
      return video.instructors.map((i) => ({
        name: i.name,
        linkedinUrl: i.linkedinUrl || '',
      }));
    }
    // Fall back to parsing the instructor string
    return (video.instructor || 'DSB Team')
      .split(',')
      .map((name) => ({ name: name.trim(), linkedinUrl: '' }));
  });
  const [description, setDescription] = useState(video.description || '');
  const [tags, setTags] = useState(video.tags.join(', '));
  const [thumbnailUrl, setThumbnailUrl] = useState(video.thumbnailUrl || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addInstructor = () => {
    setInstructorEntries([...instructorEntries, { name: '', linkedinUrl: '' }]);
  };

  const removeInstructor = (index: number) => {
    setInstructorEntries(instructorEntries.filter((_, i) => i !== index));
  };

  const updateInstructor = (index: number, field: 'name' | 'linkedinUrl', value: string) => {
    const updated = [...instructorEntries];
    updated[index] = { ...updated[index], [field]: value };
    setInstructorEntries(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const validInstructors = instructorEntries.filter((i) => i.name.trim());

    const data: UpdateVideoRequest = {
      title,
      instructor: validInstructors.map((i) => i.name).join(', '),
      instructors: validInstructors.map((i) => ({
        name: i.name.trim(),
        linkedinUrl: i.linkedinUrl.trim() || undefined,
      })),
      description,
      tags: tags.split(',').map((t) => t.trim()).filter(Boolean),
      thumbnailUrl: thumbnailUrl || undefined,
    };

    const { data: result, error: apiError } = await adminUpdateVideo(
      video.id,
      data
    );

    if (result) {
      onSaved();
      onClose();
    } else {
      setError(apiError || 'Failed to update video');
    }

    setIsSubmitting(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="relative bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-lg w-full mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
            Edit Video
          </h2>
          <span className={`text-xs px-2 py-0.5 font-medium rounded-full ${STATUS_COLORS[video.status]}`}>
            {video.status}
          </span>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              maxLength={200}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-yellow-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Instructors
            </label>
            <div className="space-y-3">
              {instructorEntries.map((entry, idx) => (
                <div key={idx} className="flex gap-2 items-start">
                  <div className="flex-1 space-y-1">
                    <input
                      type="text"
                      value={entry.name}
                      onChange={(e) => updateInstructor(idx, 'name', e.target.value)}
                      placeholder="Name"
                      className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-yellow-500 text-sm"
                    />
                    <input
                      type="url"
                      value={entry.linkedinUrl}
                      onChange={(e) => updateInstructor(idx, 'linkedinUrl', e.target.value)}
                      placeholder="LinkedIn URL (optional)"
                      className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-yellow-500 text-sm"
                    />
                  </div>
                  {instructorEntries.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeInstructor(idx)}
                      className="mt-2 p-1 text-red-500 hover:text-red-700 dark:text-red-400"
                      aria-label="Remove instructor"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>
              ))}
            </div>
            <button
              type="button"
              onClick={addInstructor}
              className="mt-2 text-sm text-yellow-600 dark:text-yellow-400 hover:text-yellow-700 font-medium"
            >
              + Add Instructor
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={5000}
              rows={4}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-yellow-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Tags (comma-separated)
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="e.g. security, jenkins, ci-cd"
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-yellow-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Thumbnail URL
            </label>
            <input
              type="text"
              value={thumbnailUrl}
              onChange={(e) => setThumbnailUrl(e.target.value)}
              placeholder="https://..."
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-yellow-500"
            />
          </div>

          {/* Info row */}
          <div className="text-xs text-gray-500 dark:text-gray-400 pt-2 border-t border-gray-200 dark:border-gray-800">
            <p>Duration: {video.durationSeconds > 0 ? formatDuration(video.durationSeconds) : 'Unknown'}</p>
            <p>Created: {new Date(video.createdAt).toLocaleString()}</p>
          </div>

          {error && (
            <p className="text-sm text-red-500 dark:text-red-400">{error}</p>
          )}

          <div className="flex justify-between pt-4">
            {video.status === 'READY' && (
              <button
                type="button"
                onClick={async () => {
                  await adminTransitionStatus(video.id, 'PUBLISHED');
                  onSaved();
                  onClose();
                }}
                className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white font-semibold rounded-lg transition-colors"
              >
                Save & Publish
              </button>
            )}
            <div className="flex gap-3 ml-auto">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-gray-900 font-semibold rounded-lg transition-colors disabled:opacity-50"
              >
                {isSubmitting ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

function AdminVideosContent() {
  const { isAdmin, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [videos, setVideos] = useState<Video[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState<VideoStatus | 'ALL'>('ALL');
  const [isLoading, setIsLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingVideo, setEditingVideo] = useState<Video | null>(null);

  const loadVideos = useCallback(async () => {
    setIsLoading(true);
    const status = statusFilter === 'ALL' ? undefined : statusFilter;
    const { data, error } = await adminListVideos(status, page, pageSize);
    if (data) {
      setVideos(data.recordings);
      setTotalCount(data.totalCount);
    }
    setIsLoading(false);
  }, [statusFilter, page, pageSize]);

  useEffect(() => {
    if (!authLoading && !isAdmin) {
      router.push('/admin');
      return;
    }
    if (isAdmin) {
      loadVideos();
    }
  }, [authLoading, isAdmin, loadVideos, router]);

  const handlePublish = async (videoId: string) => {
    await adminTransitionStatus(videoId, 'PUBLISHED');
    loadVideos();
  };

  const handleArchive = async (videoId: string) => {
    await adminTransitionStatus(videoId, 'ARCHIVED');
    loadVideos();
  };

  if (authLoading || (!isAdmin && !authLoading)) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  const startItem = (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, totalCount);

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
          Video Management
        </h1>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-gray-900 font-semibold rounded-lg transition-colors"
        >
          + Add Video
        </button>
      </div>

      {/* Status filter tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => {
              setStatusFilter(tab.value);
              setPage(1);
            }}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors whitespace-nowrap ${
              statusFilter === tab.value
                ? 'bg-yellow-500 text-gray-900'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Videos table */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Spinner size="lg" />
        </div>
      ) : videos.length === 0 ? (
        <Card>
          <p className="text-center text-gray-500 dark:text-gray-400 py-8">
            No videos found.
          </p>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                  Title
                </th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                  Instructor
                </th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                  Recorded At
                </th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                  Status
                </th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                  Duration
                </th>
                <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {videos.map((rec) => (
                <tr
                  key={rec.id}
                  className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900/50"
                >
                  <td className="py-3 px-4">
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      {rec.title}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-400">
                    {rec.instructor}
                  </td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-400">
                    {new Date(rec.recordedAt).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${STATUS_COLORS[rec.status]}`}
                    >
                      {rec.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-400">
                    {rec.durationSeconds > 0
                      ? formatDuration(rec.durationSeconds)
                      : '—'}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setEditingVideo(rec)}
                        className="text-xs px-3 py-1 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                      >
                        Edit
                      </button>
                      {rec.status === 'READY' && (
                        <button
                          onClick={() => handlePublish(rec.id)}
                          className="text-xs px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors"
                        >
                          Publish
                        </button>
                      )}
                      {(rec.status === 'PUBLISHED' ||
                        rec.status === 'READY') && (
                        <button
                          onClick={() => handleArchive(rec.id)}
                          className="text-xs px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-full hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
                        >
                          Archive
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalCount > 0 && (
        <div className="flex items-center justify-between mt-6">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Showing {startItem} to {endItem} of {totalCount} videos
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1 text-sm rounded-lg border border-gray-300 dark:border-gray-700 disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={endItem >= totalCount}
              className="px-3 py-1 text-sm rounded-lg border border-gray-300 dark:border-gray-700 disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Add Video Modal */}
      <AddVideoModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onCreated={loadVideos}
      />

      {/* Edit Video Modal */}
      {editingVideo && (
        <EditVideoModal
          video={editingVideo}
          onClose={() => setEditingVideo(null)}
          onSaved={loadVideos}
        />
      )}
    </div>
  );
}

export default function AdminVideosPage() {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-white dark:bg-gray-950">
        <NavbarWithAuth />

        <main className="pt-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <AdminVideosContent />
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
