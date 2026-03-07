'use client';

import { useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { WalkthroughLink } from './WalkthroughLink';

/**
 * WalkthroughLinkHydrator Component
 * 
 * Client-side component that finds walkthrough link placeholders in the DOM
 * and hydrates them with the actual WalkthroughLink React components.
 * 
 * This enables markdown directives like :::walkthrough{id="..."} to be
 * transformed into interactive React components after the page loads.
 * 
 * Requirements: 9.1, 9.2
 */
export function WalkthroughLinkHydrator() {
  useEffect(() => {
    // Find all walkthrough link placeholders in the DOM
    const placeholders = document.querySelectorAll('.walkthrough-link-placeholder');
    
    placeholders.forEach((placeholder) => {
      const walkthroughId = placeholder.getAttribute('data-walkthrough-id');
      
      if (!walkthroughId) {
        console.warn('Walkthrough placeholder missing data-walkthrough-id attribute');
        return;
      }

      // Create a root and render the WalkthroughLink component
      const root = createRoot(placeholder);
      root.render(<WalkthroughLink walkthroughId={walkthroughId} />);
    });
  }, []);

  // This component doesn't render anything itself
  return null;
}
