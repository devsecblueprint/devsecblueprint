'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';

interface PageNavigationProps {
  previousUrl: string | null;
  nextUrl: string | null;
  currentPosition: number;
  totalSections: number;
}

export function PageNavigation({ 
  previousUrl, 
  nextUrl, 
  currentPosition, 
  totalSections 
}: PageNavigationProps) {
  const [isSaving, setIsSaving] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  // Reset saving state when pathname changes
  useEffect(() => {
    setIsSaving(false);
  }, [pathname]);

  const handleNextClick = async (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (!nextUrl || isSaving) return;
    
    // Prevent default navigation
    e.preventDefault();
    
    // Mark as saving
    setIsSaving(true);
    
    try {
      // Call the global mark complete function and wait for backend response
      if (typeof window !== 'undefined' && (window as any).__markPageComplete) {
        await (window as any).__markPageComplete();
      }
      
      // Backend has confirmed save, now navigate
      window.location.href = nextUrl;
    } catch (error) {
      console.error('Error saving progress:', error);
      // Navigate anyway even if save fails
      window.location.href = nextUrl;
    }
  };

  const handlePreviousClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (!previousUrl) return;
    
    // Prevent default and navigate
    e.preventDefault();
    window.location.href = previousUrl;
  };

  return (
    <div className="mt-12 pt-8 border-t border-gray-300 dark:border-gray-800 flex items-center justify-between">
      {previousUrl ? (
        <Link 
          href={previousUrl}
          onClick={handlePreviousClick}
          className="flex items-center space-x-2 text-amber-500 dark:text-amber-400 hover:text-amber-600 dark:hover:text-amber-300 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          <span>Previous</span>
        </Link>
      ) : (
        <div />
      )}
      
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Section {currentPosition} of {totalSections}
      </div>
      
      {nextUrl ? (
        <Link 
          href={nextUrl}
          onClick={handleNextClick}
          className={`flex items-center space-x-2 text-amber-500 dark:text-amber-400 hover:text-amber-600 dark:hover:text-amber-300 transition-colors ${isSaving ? 'opacity-50 pointer-events-none' : ''}`}
        >
          <span>{isSaving ? 'Saving...' : 'Next'}</span>
          {isSaving ? (
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          )}
        </Link>
      ) : (
        <div />
      )}
    </div>
  );
}
