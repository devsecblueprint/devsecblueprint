/**
 * Authentication Hook
 * 
 * Provides global authentication state management using React Context.
 * Automatically checks authentication status on mount and provides
 * methods for login, logout, and auth verification.
 * 
 * Usage:
 * ```typescript
 * import { useAuth } from '@/lib/hooks/useAuth';
 * 
 * function MyComponent() {
 *   const { isAuthenticated, isLoading, userId, logout } = useAuth();
 *   
 *   if (isLoading) return <div>Loading...</div>;
 *   if (!isAuthenticated) return <div>Please log in</div>;
 *   
 *   return <div>Welcome, user {userId}!</div>;
 * }
 * ```
 */

'use client';

import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { apiClient } from '@/lib/api';

/**
 * Authentication state interface
 */
interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  userId: string | null;
  avatarUrl: string | null;
  username: string | null;
  githubUsername: string | null;
  isAdmin: boolean;
  error: string | null;
}

/**
 * Authentication context interface
 */
interface AuthContextType extends AuthState {
  checkAuth: () => Promise<void>;
  logout: () => void;
  refreshAuth: () => Promise<void>;
}

/**
 * Authentication context
 */
const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Authentication Provider Props
 */
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Authentication Provider Component
 * 
 * Wrap your app with this provider to enable authentication state management.
 * Should be placed in the root layout.tsx file.
 * 
 * @param children - Child components
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    userId: null,
    avatarUrl: null,
    username: null,
    githubUsername: null,
    isAdmin: false,
    error: null,
  });

  /**
   * Check authentication status by calling /me endpoint
   */
  const checkAuth = useCallback(async () => {
    // Only set loading to true if we don't have auth data yet
    setState(prev => ({ 
      ...prev, 
      isLoading: prev.userId === null, // Only show loading on initial check
      error: null 
    }));
    
    const { data, error } = await apiClient.checkAuth();
    
    console.log('checkAuth response:', data);
    
    if (data && data.authenticated) {
      setState({
        isAuthenticated: true,
        isLoading: false,
        userId: data.user_id,
        avatarUrl: data.avatar_url || null,
        username: data.username || null,
        githubUsername: data.github_username || null,
        isAdmin: data.is_admin || false,
        error: null,
      });
    } else {
      setState({
        isAuthenticated: false,
        isLoading: false,
        userId: null,
        avatarUrl: null,
        username: null,
        githubUsername: null,
        isAdmin: false,
        error: error || null,
      });
    }
  }, []);

  /**
   * Refresh authentication status
   * Alias for checkAuth for clarity
   */
  const refreshAuth = useCallback(async () => {
    await checkAuth();
  }, [checkAuth]);

  /**
   * Logout user
   * 
   * Calls the backend /logout endpoint to delete the JWT cookie server-side,
   * also attempts client-side deletion as a fallback, clears local auth state,
   * and redirects to home page.
   */
  const logout = useCallback(async () => {
    // Call backend to delete the cookie server-side (primary method)
    await apiClient.logout();
    
    // Also try client-side deletion as a fallback
    // Try with domain attribute (matches how cookie was set)
    document.cookie = 'dsb_token=; Max-Age=0; Path=/; Secure; SameSite=None; Domain=.devsecblueprint.com';
    // Also try without domain in case browser handled it differently
    document.cookie = 'dsb_token=; Max-Age=0; Path=/; Secure; SameSite=None';
    // Try with just basic attributes
    document.cookie = 'dsb_token=; Max-Age=0; Path=/';
    
    // Clear local auth state
    setState({
      isAuthenticated: false,
      isLoading: false,
      userId: null,
      avatarUrl: null,
      username: null,
      githubUsername: null,
      isAdmin: false,
      error: null,
    });
    
    // Redirect to home page immediately
    if (typeof window !== 'undefined') {
      window.location.href = '/';
    }
  }, []);

  /**
   * Check authentication on mount
   */
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  /**
   * Re-check authentication when window regains focus
   * This ensures auth state is fresh when user returns to the tab
   */
  useEffect(() => {
    const handleFocus = () => {
      checkAuth();
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [checkAuth]);

  return (
    <AuthContext.Provider value={{ ...state, checkAuth, logout, refreshAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * useAuth Hook
 * 
 * Access authentication state and methods from any component.
 * Must be used within an AuthProvider.
 * 
 * @returns Authentication state and methods
 * @throws Error if used outside AuthProvider
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
}
