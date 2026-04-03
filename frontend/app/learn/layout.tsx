/**
 * Learn Section Layout
 * 
 * Wraps all learning pages with authentication protection and persistent sidebar.
 * This ensures all routes under /learn/* require authentication and share the same sidebar instance.
 */

'use client';

import { AuthGuard } from '@/components/AuthGuard';
import { Sidebar } from '@/components/layout/Sidebar';
import { ReactNode, useMemo, useEffect, useState, useCallback } from 'react';
import { usePathname } from 'next/navigation';
import modulesData from '@/lib/data/modules.json';
import { useProgress } from '@/lib/hooks/useProgress';
import { useAllProgress } from '@/lib/hooks/useAllProgress';
import { Module } from '@/lib/types';
import { triggerProgressUpdate } from '@/lib/events';
import { apiClient } from '@/lib/api';

export default function LearnLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [modules, setModules] = useState(modulesData);
  const { saveProgress } = useProgress();
  const { progress, updateProgress } = useAllProgress();
  
  // Extract current page ID and content path from pathname
  const { currentPageId, contentPath, isCapstone } = useMemo(() => {
    // Remove /learn/ prefix
    const path = pathname.replace('/learn/', '');
    const parts = path.split('/');
    
    // Check if it's a capstone page
    const isCapstone = path.includes('/capstone/');
    
    // Find the actual page ID from modules.json by matching the slug
    let pageId = parts[parts.length - 1] || ''; // fallback to last part of URL
    
    for (const module of modulesData) {
      for (const page of module.pages) {
        if (page.slug === pathname) {
          pageId = page.id;
          break;
        }
      }
    }
    
    return {
      currentPageId: pageId,
      contentPath: path,
      isCapstone
    };
  }, [pathname]);

  // Save last active lesson on each page navigation (fire-and-forget)
  useEffect(() => {
    if (currentPageId) {
      apiClient.saveLastActiveLesson(currentPageId, pathname).catch(() => {
        // Silently ignore errors — sidebar and navigation continue to work
      });
    }
  }, [currentPageId, pathname]);

  // Function to mark page as complete
  const markComplete = useCallback(async (forceComplete = false) => {
    // Don't mark capstone pages as complete unless explicitly forced (via submission)
    if (isCapstone && !forceComplete) {
      return;
    }
    
    // Use currentPageId which matches the page.id field in modules.json
    // This is the content_id format stored in the database
    const progressKey = currentPageId;
    
    // Check if already completed
    if (progress[progressKey]) {
      return;
    }
    
    // Optimistically update local state immediately for instant UI feedback
    updateProgress(progressKey, true);
    
    // Save with the page ID
    await saveProgress(progressKey);
    
    // Trigger progress update event for other components (dashboard, etc.)
    triggerProgressUpdate();
  }, [currentPageId, saveProgress, progress, isCapstone, updateProgress]);

  // Update modules with progress from backend
  useEffect(() => {
    const updatedModules = modulesData.map(module => ({
      ...module,
      pages: module.pages.map(page => {
        // Check completion using both formats for backward compatibility:
        // 1. page.id (new format): e.g., "devsecops-capstone"
        // 2. slug without /learn/ prefix (old format): e.g., "devsecops/capstone/index"
        const contentPath = page.slug.replace('/learn/', '');
        const isCompleted = progress[page.id] || progress[contentPath] || false;
        return {
          ...page,
          completed: isCompleted
        };
      })
    }));
    
    setModules(updatedModules);
  }, [progress]);

  // Expose markComplete function globally for Next button
  useEffect(() => {
    (window as any).__markPageComplete = markComplete;
    return () => {
      delete (window as any).__markPageComplete;
    };
  }, [markComplete]);

  return (
    <AuthGuard>
      <Sidebar modules={modules} currentPageId={currentPageId} />
      <div className="md:ml-70">
        {children}
      </div>
    </AuthGuard>
  );
}
