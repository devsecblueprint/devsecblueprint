/**
 * Navbar with Authentication
 * 
 * Wrapper component that connects the Navbar to the authentication state.
 * Use this component instead of the base Navbar to automatically show
 * authentication status and handle logout.
 */

'use client';

import { Navbar, NavbarProps } from './Navbar';
import { useAuth } from '@/lib/hooks/useAuth';

/**
 * NavbarWithAuth Component
 * 
 * Automatically connects to authentication state and passes it to Navbar.
 * 
 * @param props - Navbar props (excluding auth-related props)
 */
export function NavbarWithAuth(props: Omit<NavbarProps, 'isAuthenticated' | 'userName' | 'userAvatar' | 'isAdmin' | 'provider' | 'onLogout'>) {
  const { isAuthenticated, userId, avatarUrl, username, isAdmin, isLoading, provider, logout } = useAuth();

  // Debug logging
  console.log('NavbarWithAuth - avatarUrl:', avatarUrl, 'username:', username);

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <Navbar
        {...props}
        isAuthenticated={false}
        userName="Loading..."
      />
    );
  }

  return (
    <Navbar
      {...props}
      isAuthenticated={isAuthenticated}
      userName={username || (userId ? `User ${userId}` : 'User')}
      userAvatar={avatarUrl || undefined}
      isAdmin={isAdmin}
      provider={provider || undefined}
      onLogout={logout}
    />
  );
}
