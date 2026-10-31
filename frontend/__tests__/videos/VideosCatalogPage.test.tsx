/**
 * Unit tests for the member Video Library catalog page (free/locked badges).
 */
import { render, screen } from '@testing-library/react';
import { useVideos } from '@/lib/hooks/useVideos';
import VideosPage from '@/app/videos/page';

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));
jest.mock('@/components/AuthGuard', () => ({
  AuthGuard: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));
jest.mock('@/components/layout/NavbarWithAuth', () => ({ NavbarWithAuth: () => <nav /> }));
jest.mock('@/lib/hooks/useAuth', () => ({ useAuth: jest.fn(() => ({})) }));
jest.mock('@/lib/hooks/useVideos', () => ({ useVideos: jest.fn() }));

const mockUseVideos = useVideos as jest.Mock;

function item(id: string, overrides: Record<string, unknown> = {}) {
  return {
    id,
    title: `Video ${id}`,
    slug: `video-${id}`,
    thumbnailUrl: null,
    durationSeconds: 1800,
    tags: [],
    accessTier: 'BUILDER',
    locked: false,
    publishedAt: '2026-01-02',
    progressPercent: 0,
    positionSeconds: null,
    lastWatchedAt: null,
    ...overrides,
  };
}

function catalog(items: ReturnType<typeof item>[]) {
  return {
    continueWatching: [],
    latest: [],
    allPublished: items,
    totalCount: items.length,
    page: 1,
    pageSize: 20,
  };
}

beforeEach(() => jest.clearAllMocks());

it('is titled "Video Library"', () => {
  mockUseVideos.mockReturnValue({ catalog: catalog([]), isLoading: false, error: null });
  render(<VideosPage />);
  expect(screen.getByRole('heading', { level: 1, name: 'Video Library' })).toBeInTheDocument();
});

it('shows Free on free videos and a Builder lock on locked videos', () => {
  mockUseVideos.mockReturnValue({
    catalog: catalog([
      item('free', { accessTier: 'FREE', locked: false }),
      item('locked', { accessTier: 'BUILDER', locked: true }),
      item('open', { accessTier: 'BUILDER', locked: false }),
    ]),
    isLoading: false,
    error: null,
  });
  render(<VideosPage />);
  expect(screen.getAllByText('Free')).toHaveLength(1);
  expect(screen.getAllByText('Builder')).toHaveLength(1);
});

it('still links locked videos to their detail page (which shows the upgrade prompt)', () => {
  mockUseVideos.mockReturnValue({
    catalog: catalog([item('locked', { locked: true })]),
    isLoading: false,
    error: null,
  });
  render(<VideosPage />);
  expect(screen.getByRole('link', { name: /video locked/i })).toHaveAttribute('href', '/videos/video-locked');
});
