'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api';

interface PathwayStatus {
  pathway_id: string;
  display_name: string;
  candidate_status: string;
  credential_id?: string | null;
}

export function CertificationsDashboardWidget() {
  const [pathways, setPathways] = useState<PathwayStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchCerts = async () => {
      try {
        const { data } = await apiClient.get<PathwayStatus[]>('/certifications');
        if (data) {
          setPathways(data);
        }
      } catch {
        // Silently fail — widget is non-critical
      } finally {
        setIsLoading(false);
      }
    };
    fetchCerts();
  }, []);

  // Don't show the widget if still loading
  if (isLoading) return null;

  const awarded = pathways.filter(p => p.candidate_status === 'AWARDED');
  const inProgress = pathways.filter(p => p.candidate_status === 'IN_PROGRESS');

  // If no activity at all, show a subtle prompt
  if (awarded.length === 0 && inProgress.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 dark:border-gray-800 p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
              <svg className="w-5 h-5 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">DSB Certifications</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Earn credentials by completing pathway capstones</p>
            </div>
          </div>
          <Link
            href="/dashboard/certifications"
            className="text-xs font-semibold text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300"
          >
            Get Started →
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-800 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Certifications</h3>
        <Link
          href="/dashboard/certifications"
          className="text-xs font-medium text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300"
        >
          View All →
        </Link>
      </div>

      <div className="space-y-3">
        {/* Awarded certs */}
        {awarded.map(p => (
          <Link
            key={p.pathway_id}
            href={`/dashboard/certifications/detail?pathway=${p.pathway_id}`}
            className="flex items-center gap-3 group"
          >
            <div className="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 group-hover:text-amber-600 dark:group-hover:text-amber-400 truncate">
                {p.display_name}
              </p>
              <p className="text-xs text-green-600 dark:text-green-400">Active</p>
            </div>
          </Link>
        ))}

        {/* In progress */}
        {inProgress.map(p => (
          <Link
            key={p.pathway_id}
            href={`/dashboard/certifications/detail?pathway=${p.pathway_id}`}
            className="flex items-center gap-3 group"
          >
            <div className="w-8 h-8 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 group-hover:text-amber-600 dark:group-hover:text-amber-400 truncate">
                {p.display_name}
              </p>
              <p className="text-xs text-amber-600 dark:text-amber-400">In Progress</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
