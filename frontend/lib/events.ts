/**
 * Custom events for cross-component communication
 */

export const BADGE_CHECK_EVENT = 'badge:check';
export const PROGRESS_UPDATE_EVENT = 'progress:update';

/**
 * Trigger a badge check event
 * This should be called after any action that might earn a badge
 * (completing a lesson, finishing a walkthrough, etc.)
 */
export function triggerBadgeCheck(): void {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent(BADGE_CHECK_EVENT));
  }
}

/**
 * Listen for badge check events
 */
export function onBadgeCheck(callback: () => void): () => void {
  if (typeof window === 'undefined') {
    return () => {};
  }

  window.addEventListener(BADGE_CHECK_EVENT, callback);
  
  // Return cleanup function
  return () => {
    window.removeEventListener(BADGE_CHECK_EVENT, callback);
  };
}

/**
 * Trigger a progress update event
 * This should be called after completing a lesson or updating progress
 */
export function triggerProgressUpdate(): void {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent(PROGRESS_UPDATE_EVENT));
  }
}

/**
 * Listen for progress update events
 */
export function onProgressUpdate(callback: () => void): () => void {
  if (typeof window === 'undefined') {
    return () => {};
  }

  window.addEventListener(PROGRESS_UPDATE_EVENT, callback);
  
  // Return cleanup function
  return () => {
    window.removeEventListener(PROGRESS_UPDATE_EVENT, callback);
  };
}
