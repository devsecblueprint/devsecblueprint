'use client';

import { useEffect, useState, useCallback } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { Module } from '@/lib/types';
import { useProgress } from '@/lib/hooks/useProgress';
import { useAllProgress } from '@/lib/hooks/useAllProgress';

interface LearningPageClientProps {
  modules: Module[];
  currentPageId: string;
  contentPath: string;
  isCapstone?: boolean;
}

export function LearningPageClient({ modules: initialModules, currentPageId, contentPath, isCapstone = false }: LearningPageClientProps) {
  const [modules, setModules] = useState(initialModules);
  const { saveProgress } = useProgress();
  const { progress } = useAllProgress();

  // Function to mark page as complete (disabled for capstone pages)
  const markComplete = useCallback(async () => {
    // Don't mark capstone pages as complete - they require submission
    if (isCapstone) {
      return;
    }
    
    // Check if already completed using either page ID or content path
    if (progress[currentPageId] || progress[contentPath]) {
      return;
    }
    // Save with the full content path for proper badge tracking
    await saveProgress(contentPath);
  }, [contentPath, saveProgress, progress, currentPageId, isCapstone]);

  // Check if user scrolled to bottom - REMOVED: Now only mark complete on Next button click
  // useEffect(() => {
  //   const handleScroll = () => {
  //     const scrollTop = window.scrollY;
  //     const windowHeight = window.innerHeight;
  //     const documentHeight = document.documentElement.scrollHeight;
  //     
  //     // Check if user is within 100px of the bottom
  //     if (scrollTop + windowHeight >= documentHeight - 100) {
  //       markComplete();
  //     }
  //   };

  //   window.addEventListener('scroll', handleScroll);
  //   return () => window.removeEventListener('scroll', handleScroll);
  // }, [markComplete]);

  // Update modules with progress from backend
  useEffect(() => {
    const updatedModules = initialModules.map(module => ({
      ...module,
      pages: module.pages.map(page => {
        // Extract the content path from the slug (remove /learn/ prefix)
        const contentPath = page.slug.replace('/learn/', '');
        // Check if this page is completed using the full path format
        const isCompleted = progress[contentPath] || false;
        return {
          ...page,
          completed: isCompleted
        };
      })
    }));
    
    setModules(updatedModules);
  }, [progress, initialModules]);

  // Expose markComplete function globally for Next button
  useEffect(() => {
    (window as any).__markPageComplete = markComplete;
    return () => {
      delete (window as any).__markPageComplete;
    };
  }, [markComplete]);

  return (
    <Sidebar
      modules={modules}
      currentPageId={currentPageId}
    />
  );
}
