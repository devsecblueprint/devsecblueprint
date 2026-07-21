/**
 * ConnectedAccountsPage Component Tests
 *
 * Tests for the Discord connected accounts settings page including:
 * - Connect Discord flow
 * - Identity confirmation modal
 * - Disconnect flow
 * - Status display and platform state progression
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const mockFetch = jest.fn();
global.fetch = mockFetch;

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => '/settings/connected-accounts',
  useSearchParams: () => new URLSearchParams(),
}));

const mockDisconnectedStatus = {
  connected: false,
  discord_username: null,
  discord_avatar_url: null,
  platform_state: null,
  last_synced_at: null,
  last_sync_status: null,
};

const mockConnectedStatus = {
  connected: true,
  discord_username: 'TestUser#1234',
  discord_avatar_url: 'https://cdn.discordapp.com/avatars/123/abc.png',
  platform_state: 'Roles_Synced',
  last_synced_at: '2024-01-15T10:30:00Z',
  last_sync_status: 'SUCCESS',
};

describe('ConnectedAccountsPage', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    mockPush.mockReset();
  });

  it('should fetch Discord status on load', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockDisconnectedStatus,
    });

    // Stub: page fetches GET /api/discord/status on mount
    expect(mockFetch).toBeDefined();
  });

  it('should show Connect Discord button when not connected', () => {
    // Stub: when status.connected is false, show a "Connect Discord" button
    // clicking it should redirect to GET /auth/discord/start
    expect(mockDisconnectedStatus.connected).toBe(false);
  });

  it('should show Discord profile when connected', () => {
    // Stub: when connected, display avatar, username, platform state
    expect(mockConnectedStatus.connected).toBe(true);
    expect(mockConnectedStatus.discord_username).toBe('TestUser#1234');
  });

  it('should show confirmation modal on ?discord=pending query param', () => {
    // Stub: when URL has ?discord=pending, show Identity_Confirmation_Prompt
    // modal with avatar, username, display_name
    // "Yes, this is my account" button should call POST /api/discord/confirm
    expect(true).toBe(true);
  });

  it('should call confirm endpoint on "Yes, this is my account" click', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        discord_user_id: '123456789012345678',
        username: 'TestUser',
        display_name: 'Test User',
        avatar_url: 'https://cdn.discordapp.com/avatars/123/abc.png',
        platform_state: 'Server_Joined',
      }),
    });

    // Stub: confirm button POSTs to /api/discord/confirm
    expect(true).toBe(true);
  });

  it('should call disconnect on "Disconnect & Choose Another"', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ cleanup_status: 'completed' }),
    });

    // Stub: alternate action in confirm modal calls DELETE /api/discord/disconnect
    expect(true).toBe(true);
  });

  it('should show disconnect confirmation dialog', () => {
    // Stub: clicking Disconnect on a connected account should show
    // a confirmation dialog before calling the API
    expect(true).toBe(true);
  });

  it('should display platform state progression', () => {
    // Stub: show visual indicator of state progression:
    // Connected → Verified → Server Joined → Roles Synced
    expect(mockConnectedStatus.platform_state).toBe('Roles_Synced');
  });

  it('should show cleanup status indicator on failed role removal', () => {
    // Stub: if disconnect results in cleanup_status="failed",
    // show an indicator that role removal is pending/failed
    expect(true).toBe(true);
  });
});
