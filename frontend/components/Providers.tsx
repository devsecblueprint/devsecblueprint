/**
 * Client-side Providers Wrapper
 * 
 * This component wraps all client-side providers (Theme, Auth, etc.)
 * and can be safely imported in the root layout.
 */

'use client';

import { ReactNode } from 'react';
import { ThemeProvider } from '@/components/ThemeProvider';
import { AuthProvider } from '@/lib/hooks/useAuth';
import { ErrorBoundary } from '@/components/ErrorBoundary';

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </AuthProvider>
    </ThemeProvider>
  );
}
