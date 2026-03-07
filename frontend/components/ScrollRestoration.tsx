'use client';

import { useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';

/**
 * ScrollRestoration component
 * 
 * Preserves scroll position when navigating away from and back to a page.
 * Stores scroll position in sessionStorage and restores it on mount.
 */
export function ScrollRestoration() {
  const pathname = usePathname();
  const isRestoringRef = useRef(false);
  const scrollKeyRef = useRef<string>('');

  useEffect(() => {
    // Disable Next.js automatic scroll restoration
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual';
    }

    const scrollKey = `scroll-${pathname}`;
    scrollKeyRef.current = scrollKey;
    
    // Restore scroll position when component mounts
    const savedPosition = sessionStorage.getItem(scrollKey);
    
    if (savedPosition && !isRestoringRef.current) {
      isRestoringRef.current = true;
      const position = parseInt(savedPosition, 10);
      
      // Restore scroll position
      const restoreScroll = () => {
        window.scrollTo(0, position);
        
        // Reset flag after restoration
        setTimeout(() => {
          isRestoringRef.current = false;
        }, 100);
      };

      // In test environment or if requestIdleCallback is not available, restore immediately
      // Otherwise wait for idle time to avoid blocking rendering
      if (typeof jest !== 'undefined' || !('requestIdleCallback' in window)) {
        // Immediate restoration for tests or browsers without requestIdleCallback
        setTimeout(restoreScroll, 0);
      } else {
        // Use requestIdleCallback for smoother UX in production
        requestIdleCallback(restoreScroll, { timeout: 100 });
      }
    } else {
      // No saved position, ensure we're at the top for new pages
      // But only if we're not in the middle of restoring
      if (!isRestoringRef.current && window.scrollY > 0) {
        // This is a new page, scroll to top
        window.scrollTo(0, 0);
      }
    }

    // Save scroll position periodically
    const handleScroll = () => {
      if (!isRestoringRef.current) {
        sessionStorage.setItem(scrollKeyRef.current, window.scrollY.toString());
      }
    };

    // Throttle scroll events
    let timeoutId: NodeJS.Timeout;
    const throttledHandleScroll = () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      timeoutId = setTimeout(handleScroll, 100);
    };

    // Save on scroll
    window.addEventListener('scroll', throttledHandleScroll, { passive: true });
    
    // Save before unload (when switching tabs or closing)
    const handleBeforeUnload = () => {
      sessionStorage.setItem(scrollKeyRef.current, window.scrollY.toString());
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    
    // Save on visibility change (when switching tabs)
    const handleVisibilityChange = () => {
      if (document.hidden) {
        sessionStorage.setItem(scrollKeyRef.current, window.scrollY.toString());
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Save scroll position when modal opens
    const handleModalOpen = () => {
      sessionStorage.setItem(scrollKeyRef.current, window.scrollY.toString());
    };

    // Restore scroll position when modal closes
    const handleModalClose = () => {
      const savedPosition = sessionStorage.getItem(scrollKeyRef.current);
      if (savedPosition) {
        const position = parseInt(savedPosition, 10);
        window.scrollTo(0, position);
      }
    };

    window.addEventListener('modal:open', handleModalOpen);
    window.addEventListener('modal:close', handleModalClose);

    return () => {
      window.removeEventListener('scroll', throttledHandleScroll);
      window.removeEventListener('beforeunload', handleBeforeUnload);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('modal:open', handleModalOpen);
      window.removeEventListener('modal:close', handleModalClose);
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [pathname]);

  return null;
}
