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
      // Decode the JWT exp claim to compute Max-Age
      let maxAge = 21600; // fallback: 6 hours in seconds
      try {
        const payload = token.split('.')[1];
        if (payload) {
          const decoded = JSON.parse(atob(payload));
          if (typeof decoded.exp === 'number') {
            maxAge = Math.max(0, decoded.exp - Math.floor(Date.now() / 1000));
          }
        }
      } catch {
        // Use default maxAge on decode failure
      }

      // Determine if we're in production (any non-localhost domain)
      const hostname = window.location.hostname;
      const isProduction = hostname !== 'localhost' && !hostname.startsWith('127.');
      
      if (isProduction) {
        // Production: Set cookie with domain for subdomain sharing
        // Extract root domain (e.g., "app.dsb-dev.com" -> ".dsb-dev.com")
        const parts = hostname.split('.');
        const rootDomain = parts.length >= 2 ? '.' + parts.slice(-2).join('.') : hostname;
        document.cookie = `dsb_session=${token}; Max-Age=${maxAge}; Path=/; Secure; SameSite=None; Domain=${rootDomain}`;
      } else {
        // Development: Set cookie without domain restriction
        document.cookie = `dsb_session=${token}; Max-Age=${maxAge}; Path=/; SameSite=Lax`;
      }

      // Refresh token cookie (dsb_refresh) is set automatically by the browser
      // from the Set-Cookie header on the backend redirect response.
      
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
