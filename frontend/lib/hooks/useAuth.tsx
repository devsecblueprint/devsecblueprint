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

import { createContext, useContext, useEffect, useState, ReactNode, useCallback, useRef } from 'react';
import { apiClient } from '@/lib/api';
import { SessionExpiryModal } from '@/components/SessionExpiryModal';

const EXPIRY_WARNING_SECONDS = 15 * 60; // 15 minutes

/**
 * Decode the `exp` claim from a JWT without verifying the signature.
 * Returns the expiration as a Unix timestamp (seconds) or null if decoding fails.
 */
function decodeJwtExp(token: string): number | null {
  try {
    const payload = token.split('.')[1];
    if (!payload) return null;
    const decoded = JSON.parse(atob(payload));
    return typeof decoded.exp === 'number' ? decoded.exp : null;
  } catch {
    return null;
  }
}

/**
 * Read a cookie value by name from document.cookie.
 */
function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

/**
 * Derive the root cookie domain from the current hostname.
 * e.g. "app.dsb-dev.com" -> ".dsb-dev.com"
 * Returns null for localhost / dev environments.
 */
function getCookieDomain(): string | null {
  if (typeof window === 'undefined') return null;
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname.startsWith('127.')) return null;
  const parts = hostname.split('.');
  return parts.length >= 2 ? '.' + parts.slice(-2).join('.') : null;
}

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
  gitlabUsername: string | null;
  bitbucketUsername: string | null;
  provider: string | null;
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
  extendSession: () => Promise<void>;
  providerUsername: string | null;
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
    gitlabUsername: null,
    bitbucketUsername: null,
    provider: null,
    isAdmin: false,
    error: null,
  });

  const [sessionExpiresAt, setSessionExpiresAt] = useState<number | null>(null);
  const [showExpiryModal, setShowExpiryModal] = useState(false);
  const [remainingSeconds, setRemainingSeconds] = useState(0);
  const expiryTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

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
        gitlabUsername: data.gitlab_username || null,
        bitbucketUsername: data.bitbucket_username || null,
        provider: data.provider || null,
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
        gitlabUsername: null,
        bitbucketUsername: null,
        provider: null,
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
    
    // Clear new session cookies
    const domain = getCookieDomain();
    const domainAttr = domain ? `; Domain=${domain}` : '';
    document.cookie = `dsb_session=; Max-Age=0; Path=/; Secure; SameSite=None${domainAttr}`;
    document.cookie = 'dsb_session=; Max-Age=0; Path=/; Secure; SameSite=None';
    document.cookie = 'dsb_session=; Max-Age=0; Path=/';
    // Clear refresh token cookies
    document.cookie = `dsb_refresh=; Max-Age=0; Path=/refresh; Secure; SameSite=None${domainAttr}`;
    document.cookie = 'dsb_refresh=; Max-Age=0; Path=/refresh; Secure; SameSite=None';
    document.cookie = 'dsb_refresh=; Max-Age=0; Path=/refresh';
    // Clear legacy cookie
    document.cookie = `dsb_token=; Max-Age=0; Path=/; Secure; SameSite=None${domainAttr}`;
    document.cookie = 'dsb_token=; Max-Age=0; Path=/; Secure; SameSite=None';
    document.cookie = 'dsb_token=; Max-Age=0; Path=/';
    
    // Clear session expiry state
    setSessionExpiresAt(null);
    setShowExpiryModal(false);

    // Clear local auth state
    setState({
      isAuthenticated: false,
      isLoading: false,
      userId: null,
      avatarUrl: null,
      username: null,
      githubUsername: null,
      gitlabUsername: null,
      bitbucketUsername: null,
      provider: null,
      isAdmin: false,
      error: null,
    });
    
    // Redirect to home page immediately
    if (typeof window !== 'undefined') {
      window.location.href = '/';
    }
  }, []);

  /**
   * Read the session token expiry from the dsb_session cookie.
   */
  const updateSessionExpiry = useCallback(() => {
    const token = getCookie('dsb_session');
    if (token) {
      const exp = decodeJwtExp(token);
      setSessionExpiresAt(exp);
    } else {
      setSessionExpiresAt(null);
      setShowExpiryModal(false);
    }
  }, []);

  /**
   * Extend the current session by calling POST /refresh.
   * On success, updates the dsb_session cookie and dismisses the expiry modal.
   */
  const extendSession = useCallback(async () => {
    const { data, error } = await apiClient.post<{ session_token: string }>('/refresh', {});

    if (error || !data?.session_token) {
      // Refresh failed — force logout
      logout();
      return;
    }

    // Set the new session cookie
    const exp = decodeJwtExp(data.session_token);
    const domain = getCookieDomain();
    const isProduction = domain !== null;
    const maxAge = exp ? exp - Math.floor(Date.now() / 1000) : 21600;

    if (isProduction) {
      document.cookie = `dsb_session=${data.session_token}; Max-Age=${maxAge}; Path=/; Secure; SameSite=None; Domain=${domain}`;
    } else {
      document.cookie = `dsb_session=${data.session_token}; Max-Age=${maxAge}; Path=/; SameSite=Lax`;
    }

    setSessionExpiresAt(exp);
    setShowExpiryModal(false);
  }, [logout]);

  /**
   * Check authentication on mount
   */
  useEffect(() => {
    checkAuth();
    updateSessionExpiry();
  }, [checkAuth, updateSessionExpiry]);

  /**
   * Session expiry monitoring timer.
   * Checks every 30 seconds normally; switches to 1-second updates when the modal is shown.
   */
  useEffect(() => {
    if (!state.isAuthenticated || sessionExpiresAt === null) {
      setShowExpiryModal(false);
      return;
    }

    const tick = () => {
      const now = Math.floor(Date.now() / 1000);
      const remaining = sessionExpiresAt - now;

      if (remaining <= 0) {
        setShowExpiryModal(false);
        logout();
        return;
      }

      setRemainingSeconds(remaining);

      if (remaining <= EXPIRY_WARNING_SECONDS) {
        setShowExpiryModal(true);
      }
    };

    // Run immediately
    tick();

    const interval = showExpiryModal ? 1000 : 30_000;
    expiryTimerRef.current = setInterval(tick, interval);

    return () => {
      if (expiryTimerRef.current) clearInterval(expiryTimerRef.current);
    };
  }, [state.isAuthenticated, sessionExpiresAt, showExpiryModal, logout]);

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

  const providerUsername = state.provider === 'bitbucket' ? state.bitbucketUsername : state.provider === 'gitlab' ? state.gitlabUsername : state.githubUsername;

  return (
    <AuthContext.Provider value={{ ...state, checkAuth, logout, refreshAuth, extendSession, providerUsername }}>
      {children}
      {showExpiryModal && (
        <SessionExpiryModal
          remainingSeconds={remainingSeconds}
          onExtendSession={extendSession}
          onLogout={logout}
        />
      )}
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
