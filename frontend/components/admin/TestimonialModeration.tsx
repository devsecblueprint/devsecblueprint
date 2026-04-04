'use client';

import React, { useEffect, useState, useRef } from 'react';
import { apiClient } from '@/lib/api';
import { AdminTestimonial } from '@/lib/types';
import { Spinner } from '@/components/ui/Spinner';
import { Badge } from '@/components/ui/Badge';
import { formatDistanceToNow } from 'date-fns';

type StatusFilter = 'all' | 'pending' | 'approved';

interface TestimonialModerationProps {
  className?: string;
}

export function TestimonialModeration({ className = '' }: TestimonialModerationProps) {
  const [testimonials, setTestimonials] = useState<AdminTestimonial[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [selectedTestimonial, setSelectedTestimonial] = useState<AdminTestimonial | null>(null);

  useEffect(() => {
    fetchTestimonials();
  }, []);

  const fetchTestimonials = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data, error: apiError } = await apiClient.getAdminTestimonials();
      if (apiError) { setError(apiError); return; }
      if (data) setTestimonials(data.testimonials);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch testimonials');
    } finally {
      setIsLoading(false);
    }
  };

  const handleModalAction = async () => {
    setSelectedTestimonial(null);
    await fetchTestimonials();
  };

  const filteredTestimonials = testimonials.filter((t) =>
    statusFilter === 'all' ? true : t.status === statusFilter
  );

  const filterTabs: { label: string; value: StatusFilter }[] = [
    { label: 'All', value: 'all' },
    { label: 'Pending', value: 'pending' },
    { label: 'Approved', value: 'approved' },
  ];

  if (isLoading) {
    return (
      <div className={className}>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Testimonial Moderation</h2>
        <div className="flex items-center justify-center py-12"><Spinner size="lg" /></div>
      </div>
    );
  }

  if (error && testimonials.length === 0) {
    return (
      <div className={className}>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Testimonial Moderation</h2>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
          <p className="text-sm text-red-800 dark:text-red-200 mb-3">{error}</p>
          <button onClick={fetchTestimonials} className="text-sm font-medium text-red-600 dark:text-red-400 hover:text-red-700 transition-colors">Try Again</button>
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
        <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100">Testimonial Moderation</h2>
        <Badge variant="default" size="sm">{testimonials.length}</Badge>
      </div>

      {error && testimonials.length > 0 && (
        <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      <div className="flex space-x-1 mb-4 border-b border-gray-200 dark:border-gray-800" role="tablist">
        {filterTabs.map((tab) => (
          <button
            key={tab.value}
            role="tab"
            aria-selected={statusFilter === tab.value}
            aria-label={`Filter testimonials by ${tab.label}`}
            onClick={() => setStatusFilter(tab.value)}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              statusFilter === tab.value
                ? 'border-amber-500 text-amber-600 dark:text-amber-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {filteredTestimonials.length === 0 ? (
        <div className="text-center py-12">
          <svg className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <p className="text-gray-600 dark:text-gray-400">
            {statusFilter === 'all' ? 'No testimonials submitted yet' : `No ${statusFilter} testimonials`}
          </p>
        </div>
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-800">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">Name</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">Quote</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">Submitted</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredTestimonials.map((t) => (
                  <tr
                    key={t.user_id}
                    onClick={() => setSelectedTestimonial(t)}
                    className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer"
                  >
                    <td className="py-3 px-4 text-sm font-medium text-gray-900 dark:text-gray-100">{t.display_name}</td>
                    <td className="py-3 px-4 text-sm text-gray-700 dark:text-gray-300 max-w-xs truncate">{t.quote}</td>
                    <td className="py-3 px-4 text-sm text-gray-500 dark:text-gray-400 whitespace-nowrap">
                      {formatDistanceToNow(new Date(t.submitted_at), { addSuffix: true })}
                    </td>
                    <td className="py-3 px-4"><StatusBadge status={t.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="md:hidden space-y-3">
            {filteredTestimonials.map((t) => (
              <div
                key={t.user_id}
                onClick={() => setSelectedTestimonial(t)}
                className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700/50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{t.display_name}</span>
                  <StatusBadge status={t.status} />
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2">&ldquo;{t.quote}&rdquo;</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {formatDistanceToNow(new Date(t.submitted_at), { addSuffix: true })}
                </p>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Review Modal */}
      {selectedTestimonial && (
        <ReviewModal
          testimonial={selectedTestimonial}
          onClose={() => setSelectedTestimonial(null)}
          onActionComplete={handleModalAction}
        />
      )}
    </div>
  );
}


function StatusBadge({ status }: { status: string }) {
  if (status === 'approved') return <Badge variant="success" size="sm">Approved</Badge>;
  return <Badge variant="warning" size="sm">Pending</Badge>;
}

function ReviewModal({
  testimonial,
  onClose,
  onActionComplete,
}: {
  testimonial: AdminTestimonial;
  onClose: () => void;
  onActionComplete: () => void;
}) {
  const [note, setNote] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEscape);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [onClose]);

  const handleAction = async (action: string) => {
    setIsProcessing(true);
    setActionError(null);
    try {
      const { error } = await apiClient.updateTestimonialStatus(
        testimonial.user_id,
        action,
        note.trim() || undefined
      );
      if (error) {
        setActionError(error);
        return;
      }
      onActionComplete();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Action failed');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby="review-modal-title">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div ref={modalRef} className="relative w-full max-w-lg bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-800">
          <h3 id="review-modal-title" className="text-lg font-semibold text-gray-900 dark:text-gray-100">Review Testimonial</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" aria-label="Close modal">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">{testimonial.display_name}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 font-mono mt-0.5">{testimonial.user_id}</p>
            </div>
            <StatusBadge status={testimonial.status} />
          </div>

          {testimonial.linkedin_url && (
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">LinkedIn</span>
              <a href={testimonial.linkedin_url} target="_blank" rel="noopener noreferrer" className="block mt-1 text-sm text-amber-600 dark:text-amber-400 hover:underline break-all">
                {testimonial.linkedin_url}
              </a>
            </div>
          )}

          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Testimonial</span>
            <div className="mt-2 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-amber-400">
              <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed italic whitespace-pre-wrap">
                &ldquo;{testimonial.quote}&rdquo;
              </p>
            </div>
          </div>

          <div className="flex gap-4 text-xs text-gray-500 dark:text-gray-400">
            <div>
              <span className="font-semibold uppercase tracking-wider">Submitted</span>
              <p className="mt-0.5 text-gray-700 dark:text-gray-300">{new Date(testimonial.submitted_at).toLocaleString()}</p>
            </div>
            {testimonial.reviewed_by && (
              <div>
                <span className="font-semibold uppercase tracking-wider">Reviewed by</span>
                <p className="mt-0.5 text-gray-700 dark:text-gray-300">{testimonial.reviewed_by}</p>
              </div>
            )}
          </div>

          {testimonial.admin_note && (
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">Previous Note</span>
              <p className="mt-1 text-sm text-blue-900 dark:text-blue-100 italic">{testimonial.admin_note}</p>
            </div>
          )}

          {/* Note input */}
          <div>
            <label htmlFor="admin-note" className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
              Admin Note (optional)
            </label>
            <textarea
              id="admin-note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Leave a note for this action..."
              rows={3}
              className="mt-1 w-full text-sm rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-500 resize-vertical"
            />
          </div>

          {actionError && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-800 dark:text-red-200">{actionError}</p>
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div className="flex flex-wrap gap-2 p-6 border-t border-gray-200 dark:border-gray-800">
          {testimonial.status === 'pending' && (
            <>
              <button
                onClick={() => handleAction('approve')}
                disabled={isProcessing}
                aria-label={`Approve testimonial from ${testimonial.display_name}`}
                className="px-4 py-2 text-sm font-medium rounded-lg bg-green-600 text-white hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                {isProcessing ? 'Processing...' : 'Approve'}
              </button>
              <button
                onClick={() => handleAction('reject')}
                disabled={isProcessing}
                aria-label={`Reject testimonial from ${testimonial.display_name}`}
                className="px-4 py-2 text-sm font-medium rounded-lg bg-red-600 text-white hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                Reject
              </button>
            </>
          )}
          {testimonial.status === 'approved' && (
            <button
              onClick={() => handleAction('revoke')}
              disabled={isProcessing}
              aria-label={`Revoke testimonial from ${testimonial.display_name}`}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-orange-600 text-white hover:bg-orange-700 transition-colors disabled:opacity-50"
            >
              Revoke
            </button>
          )}
          <button
            onClick={onClose}
            disabled={isProcessing}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 ml-auto"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
