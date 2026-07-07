/**
 * Navbar with Authentication
 * 
 * Wrapper component that connects the Navbar to the authentication state.
 * Use this component instead of the base Navbar to automatically show
 * authentication status and handle logout.
 */

'use client';

import { useState, useEffect } from 'react';
import { Navbar, NavbarProps } from './Navbar';
import { useAuth } from '@/lib/hooks/useAuth';
import { apiClient } from '@/lib/api';

/**
 * NavbarWithAuth Component
 * 
 * Automatically connects to authentication state and passes it to Navbar.
 * 
 * @param props - Navbar props (excluding auth-related props)
 */
export function NavbarWithAuth(props: Omit<NavbarProps, 'isAuthenticated' | 'userName' | 'userAvatar' | 'isAdmin' | 'provider' | 'membershipTier' | 'onLogout'>) {
  const { isAuthenticated, userId, avatarUrl, username, isAdmin, isLoading, provider, logout } = useAuth();
  const [membershipTier, setMembershipTier] = useState<string | undefined>(undefined);

  useEffect(() => {
    async function fetchTier() {
      if (!isAuthenticated) return;
      const { data } = await apiClient.get<{ membership_tier: string }>('/api/stripe/subscription');
      if (data?.membership_tier) {
        setMembershipTier(data.membership_tier);
      }
    }
    fetchTier();
  }, [isAuthenticated]);

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
      membershipTier={membershipTier}
      onLogout={logout}
    />
  );
}
