/**
 * Unit tests for VideoPageContent (authenticated player page).
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useVideo } from '@/lib/hooks/useVideos';
import { usePlaybackToken, usePlaybackProgress } from '@/lib/hooks/usePlaybackProgress';
import { VideoPageContent } from '@/app/videos/[slug]/VideoPageContent';

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));
jest.mock('@/components/AuthGuard', () => ({ AuthGuard: ({ children }: { children: React.ReactNode }) => <>{children}</> }));
jest.mock('@/components/layout/NavbarWithAuth', () => ({ NavbarWithAuth: () => <nav /> }));
jest.mock('../components/RestrictedAccess', () => ({ RestrictedAccess: () => <div data-testid="restricted" /> }), { virtual: true });
jest.mock('@/app/videos/components/RestrictedAccess', () => ({ RestrictedAccess: () => <div data-testid="restricted" /> }), { virtual: true });
jest.mock('@/lib/hooks/useVideos', () => ({ useVideo: jest.fn() }));
jest.mock('@/lib/hooks/usePlaybackProgress', () => ({
  usePlaybackToken: jest.fn(),
  usePlaybackProgress: jest.fn(),
}));

const mockUseVideo = useVideo as jest.Mock;
const mockToken = usePlaybackToken as jest.Mock;
const mockProgress = usePlaybackProgress as jest.Mock;

function video(overrides: Record<string, unknown> = {}) {
  return {
    id: 'v1',
    title: 'Securing CI/CD',
    slug: 'securing-cicd',
    description: 'Great session',
    durationSeconds: 3661,
    instructor: 'Ada',
    instructors: [{ name: 'Ada', linkedinUrl: 'https://linkedin.com/in/ada' }],
    tags: ['ci', 'security'],
    resources: [{ title: 'Slides', url: 'https://x/slides' }],
    recordedAt: '2026-01-01',
    publishedAt: '2026-01-02',
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  Object.defineProperty(window, 'location', { writable: true, value: { pathname: '/videos/securing-cicd' } });
  // Player hooks default to loaded with a token so PlayerSection renders the iframe.
  mockToken.mockReturnValue({ token: 'tok', isLoading: false, error: null });
  mockProgress.mockReturnValue({ progress: null, isLoading: false, saveCurrentProgress: jest.fn() });
});

it('shows a spinner while the video is loading', () => {
  mockUseVideo.mockReturnValue({ video: null, isLoading: true, error: null });
  const { container } = render(<VideoPageContent />);
  expect(container.querySelector('.animate-spin')).toBeInTheDocument();
});

it('renders a restricted-access view on a 403 entitlement error', () => {
  mockUseVideo.mockReturnValue({ video: null, isLoading: false, error: 'HTTP 403: entitlement required' });
  render(<VideoPageContent />);
  expect(screen.getByTestId('restricted')).toBeInTheDocument();
});

it('shows a generic error message for non-403 errors', () => {
  mockUseVideo.mockReturnValue({ video: null, isLoading: false, error: 'server exploded' });
  render(<VideoPageContent />);
  expect(screen.getByText('server exploded')).toBeInTheDocument();
});

it('renders the video with metadata and tabs', () => {
  mockUseVideo.mockReturnValue({ video: video(), isLoading: false, error: null });
  render(<VideoPageContent />);
  expect(screen.getByRole('heading', { name: 'Securing CI/CD' })).toBeInTheDocument();
  // Overview tab shows the description
  expect(screen.getByText('Great session')).toBeInTheDocument();
});

it('switches to the Resources tab', () => {
  mockUseVideo.mockReturnValue({ video: video(), isLoading: false, error: null });
  render(<VideoPageContent />);
  fireEvent.click(screen.getByRole('button', { name: /resources/i }));
  expect(screen.getByText('Slides')).toBeInTheDocument();
});

it('switches to the Instructor tab with LinkedIn link', () => {
  mockUseVideo.mockReturnValue({ video: video(), isLoading: false, error: null });
  render(<VideoPageContent />);
  fireEvent.click(screen.getByRole('button', { name: /instructor/i }));
  const links = screen.getAllByRole('link', { name: /linkedin/i });
  expect(links[0]).toHaveAttribute('href', 'https://linkedin.com/in/ada');
});
