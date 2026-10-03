/**
 * Unit tests for VideoPreviewContent.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { useAuth } from '@/lib/hooks/useAuth';
import { fetchPublicVideo } from '@/lib/video-client';
import { VideoPreviewContent } from '@/app/videos/preview/[slug]/VideoPreviewContent';

const replaceMock = jest.fn();
jest.mock('next/navigation', () => ({ useRouter: () => ({ replace: replaceMock }) }));
jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));
jest.mock('@/components/layout/NavbarWithAuth', () => ({ NavbarWithAuth: () => <nav /> }));
jest.mock('@/lib/hooks/useAuth', () => ({ useAuth: jest.fn() }));
jest.mock('@/lib/video-client', () => ({ fetchPublicVideo: jest.fn() }));

const mockUseAuth = useAuth as jest.Mock;
const mockFetch = fetchPublicVideo as jest.Mock;

function setPath(path: string) {
  Object.defineProperty(window, 'location', { writable: true, value: { pathname: path } });
}

function video(overrides: Record<string, unknown> = {}) {
  return {
    id: 'v1',
    title: 'Securing CI/CD',
    slug: 'securing-cicd',
    description: 'A deep dive',
    thumbnailUrl: null,
    durationSeconds: 3900,
    tags: ['ci', 'security'],
    instructor: 'Ada',
    instructors: [{ name: 'Ada', linkedinUrl: 'https://linkedin.com/in/ada' }],
    recordedAt: '2026-01-01',
    publishedAt: '2026-01-02',
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  setPath('/videos/preview/securing-cicd');
});

it('renders the preview for an unauthenticated user', async () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: false });
  mockFetch.mockResolvedValue({ data: video(), statusCode: 200 });
  render(<VideoPreviewContent />);
  expect(await screen.findByRole('heading', { name: 'Securing CI/CD' })).toBeInTheDocument();
  expect(screen.getByText('A deep dive')).toBeInTheDocument();
  // duration 3900s -> 1h 5m
  expect(screen.getAllByText('1h 5m').length).toBeGreaterThan(0);
});

it('redirects authenticated users to the full video page', async () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: true });
  mockFetch.mockResolvedValue({ data: video(), statusCode: 200 });
  render(<VideoPreviewContent />);
  await waitFor(() => expect(replaceMock).toHaveBeenCalledWith('/videos/securing-cicd'));
});

it('shows a not-found message when the fetch fails', async () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: false });
  mockFetch.mockResolvedValue({ error: 'gone', statusCode: 404 });
  render(<VideoPreviewContent />);
  expect(await screen.findByText('Video Not Found')).toBeInTheDocument();
});

it('shows instructor LinkedIn links', async () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: false });
  mockFetch.mockResolvedValue({ data: video(), statusCode: 200 });
  render(<VideoPreviewContent />);
  await screen.findByRole('heading', { name: 'Securing CI/CD' });
  expect(screen.getByLabelText('Ada on LinkedIn')).toHaveAttribute('href', 'https://linkedin.com/in/ada');
});

it('renders tags and a membership CTA', async () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: false });
  mockFetch.mockResolvedValue({ data: video(), statusCode: 200 });
  render(<VideoPreviewContent />);
  await screen.findByRole('heading', { name: 'Securing CI/CD' });
  expect(screen.getByText('ci')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /view membership options/i })).toBeInTheDocument();
});
