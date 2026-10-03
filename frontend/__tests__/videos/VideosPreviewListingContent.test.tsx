/**
 * Unit tests for VideosPreviewListingContent.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { useAuth } from '@/lib/hooks/useAuth';
import { fetchPublicVideos } from '@/lib/video-client';
import { VideosPreviewListingContent } from '@/app/videos/preview/VideosPreviewListingContent';

const replaceMock = jest.fn();
jest.mock('next/navigation', () => ({ useRouter: () => ({ replace: replaceMock }) }));
jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));
jest.mock('@/components/layout/NavbarWithAuth', () => ({ NavbarWithAuth: () => <nav /> }));
jest.mock('@/components/layout/Footer', () => ({ Footer: () => <footer /> }));
jest.mock('@/lib/hooks/useAuth', () => ({ useAuth: jest.fn() }));
jest.mock('@/lib/video-client', () => ({ fetchPublicVideos: jest.fn() }));

const mockUseAuth = useAuth as jest.Mock;
const mockFetch = fetchPublicVideos as jest.Mock;

function video(id: string, overrides: Record<string, unknown> = {}) {
  return {
    id,
    title: `Video ${id}`,
    slug: `video-${id}`,
    description: 'desc',
    thumbnailUrl: null,
    durationSeconds: 1800,
    tags: ['x'],
    instructor: 'Ada',
    instructors: [],
    recordedAt: '2026-01-01',
    publishedAt: '2026-01-02',
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  mockUseAuth.mockReturnValue({ isAuthenticated: false });
});

it('renders the video grid', async () => {
  mockFetch.mockResolvedValue({ data: { videos: [video('1'), video('2')] }, statusCode: 200 });
  render(<VideosPreviewListingContent />);
  expect(await screen.findByText('Video 1')).toBeInTheDocument();
  expect(screen.getByText('Video 2')).toBeInTheDocument();
});

it('shows an empty state', async () => {
  mockFetch.mockResolvedValue({ data: { videos: [] }, statusCode: 200 });
  render(<VideosPreviewListingContent />);
  expect(await screen.findByText('No videos available yet')).toBeInTheDocument();
});

it('shows an error state', async () => {
  mockFetch.mockResolvedValue({ error: 'boom', statusCode: 500 });
  render(<VideosPreviewListingContent />);
  expect(await screen.findByText('boom')).toBeInTheDocument();
});

it('redirects authenticated users to the full catalog', async () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: true });
  mockFetch.mockResolvedValue({ data: { videos: [] }, statusCode: 200 });
  render(<VideosPreviewListingContent />);
  await waitFor(() => expect(replaceMock).toHaveBeenCalledWith('/videos'));
});

it('always renders the membership CTA', async () => {
  mockFetch.mockResolvedValue({ data: { videos: [video('1')] }, statusCode: 200 });
  render(<VideosPreviewListingContent />);
  await screen.findByText('Video 1');
  expect(screen.getByRole('link', { name: /view membership options/i })).toBeInTheDocument();
});
