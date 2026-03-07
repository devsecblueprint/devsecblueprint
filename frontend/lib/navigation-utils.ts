/**
 * Navigation utilities for learning pages
 * 
 * Provides functions to get next/previous pages for navigation.
 */

import modulesData from '@/lib/data/modules.json';
import { Module, Page } from '@/lib/types';

/**
 * Get all pages in order across all modules
 */
export function getAllPagesInOrder(): Page[] {
  const modules = modulesData as Module[];
  
  // Sort modules by order
  const sortedModules = [...modules].sort((a, b) => a.order - b.order);
  
  // Flatten and sort pages
  const allPages: Page[] = [];
  sortedModules.forEach(module => {
    const sortedPages = [...module.pages].sort((a, b) => a.order - b.order);
    allPages.push(...sortedPages);
  });
  
  return allPages;
}

/**
 * Get the next and previous pages for a given page slug
 */
export function getAdjacentPages(currentSlug: string): {
  previousPage?: { title: string; slug: string };
  nextPage?: { title: string; slug: string };
} {
  const allPages = getAllPagesInOrder();
  const currentIndex = allPages.findIndex(page => page.slug === currentSlug);
  
  if (currentIndex === -1) {
    return {};
  }
  
  const previousPage = currentIndex > 0 ? allPages[currentIndex - 1] : undefined;
  const nextPage = currentIndex < allPages.length - 1 ? allPages[currentIndex + 1] : undefined;
  
  return {
    previousPage: previousPage ? { title: previousPage.title, slug: previousPage.slug } : undefined,
    nextPage: nextPage ? { title: nextPage.title, slug: nextPage.slug } : undefined,
  };
}
