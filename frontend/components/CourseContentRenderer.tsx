/**
 * Course Content Renderer Component
 * 
 * Wraps course content HTML and adds interactive features:
 * - Image click handlers for lightbox zoom
 * - Centers images
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import { ImageLightbox } from '@/components/ui/ImageLightbox';

interface CourseContentRendererProps {
  html: string;
}

export function CourseContentRenderer({ html }: CourseContentRendererProps) {
  const [lightboxImage, setLightboxImage] = useState<{ src: string; alt: string } | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  // Add click handlers to images after HTML is rendered
  useEffect(() => {
    if (!contentRef.current) return;

    const images = contentRef.current.querySelectorAll('img');
    
    const handleImageClick = (e: Event) => {
      const img = e.target as HTMLImageElement;
      setLightboxImage({
        src: img.src,
        alt: img.alt || 'Image from course content'
      });
    };

    images.forEach(img => {
      img.addEventListener('click', handleImageClick);
    });

    return () => {
      images.forEach(img => {
        img.removeEventListener('click', handleImageClick);
      });
    };
  }, [html]);

  return (
    <>
      <div
        ref={contentRef}
        className="prose prose-lg dark:prose-invert max-w-none
          [&_.admonition]:p-4 [&_.admonition]:my-4 [&_.admonition]:rounded-lg [&_.admonition]:border-l-4
          [&_.admonition-heading]:mb-2
          [&_.admonition-heading_h5]:m-0 [&_.admonition-heading_h5]:font-semibold [&_.admonition-heading_h5]:text-base
          [&_.admonition-content]:text-sm
          [&_.admonition-note]:bg-blue-50 [&_.admonition-note]:border-blue-500 [&_.admonition-note]:text-blue-900
          dark:[&_.admonition-note]:bg-blue-950 dark:[&_.admonition-note]:text-blue-100
          [&_.admonition-tip]:bg-green-50 [&_.admonition-tip]:border-green-500 [&_.admonition-tip]:text-green-900
          dark:[&_.admonition-tip]:bg-green-950 dark:[&_.admonition-tip]:text-green-100
          [&_.admonition-important]:bg-purple-50 [&_.admonition-important]:border-purple-500 [&_.admonition-important]:text-purple-900
          dark:[&_.admonition-important]:bg-purple-950 dark:[&_.admonition-important]:text-purple-100
          [&_.admonition-warning]:bg-yellow-50 [&_.admonition-warning]:border-yellow-500 [&_.admonition-warning]:text-yellow-900
          dark:[&_.admonition-warning]:bg-yellow-950 dark:[&_.admonition-warning]:text-yellow-100
          [&_.admonition-danger]:bg-red-50 [&_.admonition-danger]:border-red-500 [&_.admonition-danger]:text-red-900
          dark:[&_.admonition-danger]:bg-red-950 dark:[&_.admonition-danger]:text-red-100
          prose-img:mx-auto prose-img:cursor-pointer"
        dangerouslySetInnerHTML={{ __html: html }}
      />
      
      <ImageLightbox
        src={lightboxImage?.src || ''}
        alt={lightboxImage?.alt || ''}
        isOpen={!!lightboxImage}
        onClose={() => setLightboxImage(null)}
      />
    </>
  );
}
