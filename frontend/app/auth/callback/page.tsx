'use client';

import { useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';

/**
 * OAuth Callback Handler Component
 */
function AuthCallbackContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const token = searchParams.get('token');

    if (token) {
      // Set the JWT as a cookie
      // Determine if we're in production or development
      const isProduction = window.location.hostname.includes('devsecblueprint.com');
      
      if (isProduction) {
        // Production: Set cookie with domain for subdomain sharing
        document.cookie = `dsb_token=${token}; Max-Age=3600; Path=/; Secure; SameSite=None; Domain=.devsecblueprint.com`;
      } else {
        // Development: Set cookie without domain restriction
        document.cookie = `dsb_token=${token}; Max-Age=3600; Path=/; SameSite=Lax`;
      }
      
      // Small delay to ensure cookie is set before redirect
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 100);
    } else {
      // No token found, redirect to home
      router.push('/');
    }
  }, [searchParams, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-white dark:bg-gray-950">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-400"></div>
        <p className="mt-4 text-gray-600 dark:text-gray-400">Completing sign in...</p>
      </div>
    </div>
  );
}

/**
 * OAuth Callback Handler Page
 * 
 * This page receives the JWT token from the backend OAuth callback,
 * sets it as a cookie, and redirects to the dashboard.
 */
export default function AuthCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-white dark:bg-gray-950">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-400"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    }>
      <AuthCallbackContent />
    </Suspense>
  );
}

// Disable static generation for this page since it needs query parameters
export const dynamic = 'force-dynamic';
