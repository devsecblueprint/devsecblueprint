'use client';

import { useEffect } from 'react';

/**
 * Component that automatically adds target="_blank" and rel="noopener noreferrer"
 * to all external links in the page content.
 * 
 * This runs after the page loads and processes all links in .prose content.
 */
export function ExternalLinkHandler() {
  useEffect(() => {
    // Find all links in prose content
    const proseElements = document.querySelectorAll('.prose');
    
    proseElements.forEach((prose) => {
      const links = prose.querySelectorAll('a[href]');
      
      links.forEach((link) => {
        const href = link.getAttribute('href');
        
        // Check if it's an external link (starts with http:// or https://)
        if (href && (href.startsWith('http://') || href.startsWith('https://'))) {
          // Check if it's not an internal link (contains our domain)
          const isInternal = href.includes('devsecblueprint') || 
                           href.includes('localhost') ||
                           href.includes('127.0.0.1');
          
          if (!isInternal) {
            // Add target="_blank" to open in new tab
            link.setAttribute('target', '_blank');
            // Add rel="noopener noreferrer" for security
            link.setAttribute('rel', 'noopener noreferrer');
          }
        }
      });
    });
  }, []); // Run once on mount

  return null; // This component doesn't render anything
}
