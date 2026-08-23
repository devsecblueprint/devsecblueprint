/**
 * Tests for the Videos Catalog page and RestrictedAccess component.
 *
 * Validates: Requirements 9.1, 10.1, 11.1
 */

import React from 'react';
import { render, screen, waitFor } from '../test-utils';

// Mock the video client
jest.mock('@/lib/video-client', () => ({
  fetchCatalog: jest.fn(),
  fetchVideo: jest.fn(),
  requestPlaybackToken: jest.fn(),
  fetchProgress: jest.fn(),
  saveProgress: jest.fn(),
}));

// Mock useAuth to control authentication state
jest.mock('@/lib/hooks/useAuth', () => {
  const actual = jest.requireActual('@/lib/hooks/useAuth');
  return {
    ...actual,
    useAuth: () => ({
      isAuthenticated: true,
      isLoading: false,
      isAdmin: false,
      userId: 'test-user-123',
      username: 'testuser',
      avatarUrl: null,
      githubUsername: 'testuser',
      gitlabUsername: null,
      bitbucketUsername: null,
      provider: 'github',
      error: null,
      checkAuth: jest.fn(),
      logout: jest.fn(),
      refreshAuth: jest.fn(),
      extendSession: jest.fn(),
      providerUsername: 'testuser',
    }),
    AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  };
});

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
  }),
  usePathname: () => '/videos',
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({ slug: 'test-video' }),
}));

import { fetchCatalog } from '@/lib/video-client';
import { RestrictedAccess } from '@/app/videos/components/RestrictedAccess';

describe('RestrictedAccess Component', () => {
  it('renders lock icon and heading', () => {
    render(<RestrictedAccess />);

    expect(
      screen.getByText('Video Access Restricted')
    ).toBeInTheDocument();
  });

  it('renders membership options link', () => {
    render(<RestrictedAccess />);

    const link = screen.getByText('View Membership Options');
    expect(link).toBeInTheDocument();
    expect(link.closest('a')).toHaveAttribute('href', '/pricing');
  });

  it('displays explanation message', () => {
    render(<RestrictedAccess />);

    expect(
      screen.getByText(/Builder Session Videos are available exclusively/)
    ).toBeInTheDocument();
  });
});

describe('Videos Catalog', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows loading state initially', async () => {
    (fetchCatalog as jest.Mock).mockReturnValue(
      new Promise(() => {}) // Never resolves = stays loading
    );

    // Import dynamically to get fresh module
    const { default: VideosPage } = await import(
      '@/app/videos/page'
    );
    render(<VideosPage />);

    // AuthGuard renders content since we mocked isAuthenticated=true
    // The CatalogContent component should show loading state
    await waitFor(() => {
      expect(screen.getByRole('status')).toBeInTheDocument();
    });
  });

  it('renders catalog sections when data loads', async () => {
    (fetchCatalog as jest.Mock).mockResolvedValue({
      data: {
        continueWatching: [],
        latest: [
          {
            id: 'rec-1',
            title: 'Test Video',
            slug: 'test-video',
            thumbnailUrl: null,
            durationSeconds: 3600,
            tags: ['security'],
            publishedAt: '2025-01-01T00:00:00Z',
            progressPercent: 0,
            positionSeconds: null,
            lastWatchedAt: null,
          },
        ],
        allPublished: [
          {
            id: 'rec-1',
            title: 'Test Video',
            slug: 'test-video',
            thumbnailUrl: null,
            durationSeconds: 3600,
            tags: ['security'],
            publishedAt: '2025-01-01T00:00:00Z',
            progressPercent: 0,
            positionSeconds: null,
            lastWatchedAt: null,
          },
        ],
        totalCount: 1,
        page: 1,
        pageSize: 20,
      },
      error: undefined,
    });

    const { default: VideosPage } = await import(
      '@/app/videos/page'
    );
    render(<VideosPage />);

    await waitFor(() => {
      expect(screen.getByText('Test Video')).toBeInTheDocument();
    });

    expect(screen.getByText('Latest Videos')).toBeInTheDocument();
  });

  it('shows restricted access on 403 error', async () => {
    (fetchCatalog as jest.Mock).mockResolvedValue({
      data: undefined,
      error: 'HTTP 403: Insufficient entitlement for videos',
      statusCode: 403,
    });

    const { default: VideosPage } = await import(
      '@/app/videos/page'
    );
    render(<VideosPage />);

    await waitFor(() => {
      expect(
        screen.getByText('Video Access Restricted')
      ).toBeInTheDocument();
    });
  });

  it('renders search input', async () => {
    (fetchCatalog as jest.Mock).mockResolvedValue({
      data: {
        continueWatching: [],
        latest: [],
        allPublished: [],
        totalCount: 0,
        page: 1,
        pageSize: 20,
      },
    });

    const { default: VideosPage } = await import(
      '@/app/videos/page'
    );
    render(<VideosPage />);

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText('Search videos...')
      ).toBeInTheDocument();
    });
  });
});
