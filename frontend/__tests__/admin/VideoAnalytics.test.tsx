/**
 * Tests for the VideoAnalytics admin component.
 */
import { render, screen, fireEvent, waitFor, within, act } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { VideoAnalytics } from '@/components/admin/VideoAnalytics';
import type { VideoAnalyticsItem, VideoAnalyticsResponse } from '@/lib/types';

jest.mock('@/lib/api', () => ({
  apiClient: { getVideoAnalytics: jest.fn() },
}));

const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function video(overrides: Partial<VideoAnalyticsItem>): VideoAnalyticsItem {
  return {
    id: 'v',
    title: 'Video',
    slug: 'video',
    status: 'PUBLISHED',
    access_tier: 'FREE',
    unique_viewers: 0,
    completed: 0,
    completion_rate: 0,
    avg_best_progress: 0,
    last_watched_at: null,
    ...overrides,
  };
}

const ZERO_TRUST = video({
  id: 'v1',
  title: 'Zero Trust Intro',
  access_tier: 'BUILDER',
  unique_viewers: 10,
  completed: 6,
  completion_rate: 60,
  avg_best_progress: 75,
  last_watched_at: '2026-03-10T12:00:00Z',
});
const DOCKER = video({
  id: 'v2',
  title: 'Docker Hardening',
  access_tier: 'FREE',
  unique_viewers: 25,
  completed: 20,
  completion_rate: 80,
  avg_best_progress: 90,
  last_watched_at: '2026-03-12T12:00:00Z',
});
const SECRETS = video({
  id: 'v3',
  title: 'Secrets Management',
  access_tier: 'BUILDER',
});
const SAST = video({
  id: 'v4',
  title: 'SAST Basics',
  access_tier: 'FREE',
  unique_viewers: 5,
  completed: 1,
  completion_rate: 20,
  avg_best_progress: 40,
  last_watched_at: '2026-03-01T12:00:00Z',
});

function sample(overrides: Partial<VideoAnalyticsResponse> = {}): VideoAnalyticsResponse {
  return {
    generated_at: new Date().toISOString(),
    stale: false,
    totals: {
      distinct_viewers: 31,
      active_7d: 12,
      active_30d: 27,
      completions: 27,
      completion_rate: 68,
    },
    by_tier: {
      FREE: { viewers: 30, completions: 21, completion_rate: 70 },
      BUILDER: { viewers: 10, completions: 6, completion_rate: 60 },
    },
    top_videos: [DOCKER, ZERO_TRUST, SAST],
    videos: [ZERO_TRUST, DOCKER, SECRETS, SAST],
    ...overrides,
  };
}

function mockOk(data: VideoAnalyticsResponse) {
  mockApi.getVideoAnalytics.mockResolvedValue({ data, statusCode: 200 });
}

/** Titles of the rows currently shown in the "All videos" table, in order. */
function tableTitles(): string[] {
  const table = screen.getByRole('table');
  return within(table)
    .getAllByRole('rowheader')
    .map((cell) => cell.textContent ?? '');
}

function headerCell(name: string) {
  return screen.getByRole('columnheader', { name });
}

beforeEach(() => {
  jest.clearAllMocks();
});

afterEach(() => {
  jest.useRealTimers();
});

describe('states', () => {
  it('shows a loading skeleton while the request is pending', () => {
    mockApi.getVideoAnalytics.mockReturnValue(new Promise(() => undefined));
    render(<VideoAnalytics />);
    expect(screen.getByLabelText('Loading video analytics')).toHaveAttribute('aria-busy', 'true');
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('shows the error and retries on "Try again"', async () => {
    mockApi.getVideoAnalytics.mockResolvedValueOnce({ error: 'Server blew up', statusCode: 500 });
    render(<VideoAnalytics />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Server blew up');

    mockOk(sample());
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }));
    expect(await screen.findByRole('table')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(mockApi.getVideoAnalytics).toHaveBeenCalledTimes(2);
  });

  it('shows a friendly message for a 503', async () => {
    mockApi.getVideoAnalytics.mockResolvedValue({ error: 'Analytics not ready', statusCode: 503 });
    render(<VideoAnalytics />);
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Analytics are still being prepared, try again in a moment'
    );
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument();
  });

  it('shows an error when the request rejects', async () => {
    mockApi.getVideoAnalytics.mockRejectedValue(new Error('network down'));
    render(<VideoAnalytics />);
    expect(await screen.findByRole('alert')).toHaveTextContent('network down');
  });

  it('shows the empty state when there are no videos', async () => {
    mockOk(sample({ videos: [], top_videos: [] }));
    render(<VideoAnalytics />);
    expect(await screen.findByText('No videos yet')).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });
});

describe('content', () => {
  beforeEach(() => {
    mockOk(sample());
  });

  it('renders the four summary cards', async () => {
    render(<VideoAnalytics />);
    await screen.findByRole('table');
    expect(screen.getByText('Distinct viewers').previousElementSibling).toHaveTextContent('31');
    expect(screen.getByText('Active last 7 days').previousElementSibling).toHaveTextContent('12');
    expect(screen.getByText('Active last 30 days').previousElementSibling).toHaveTextContent('27');
    // "Completion rate" also labels each tier block, the card comes first
    expect(screen.getAllByText('Completion rate')[0].previousElementSibling).toHaveTextContent('68%');
  });

  it('renders the most watched list in order with viewer counts', async () => {
    render(<VideoAnalytics />);
    await screen.findByRole('table');
    const list = screen.getByRole('list', { name: 'Most watched videos' });
    const items = within(list).getAllByRole('listitem');
    expect(items).toHaveLength(3);
    expect(items[0]).toHaveTextContent('Docker Hardening');
    expect(items[0]).toHaveTextContent('25 viewers');
    expect(items[1]).toHaveTextContent('Zero Trust Intro');
    expect(items[2]).toHaveTextContent('SAST Basics');
    expect(items[2]).toHaveTextContent('5 viewers');
  });

  it('renders the access tier panel for Free and Builder', async () => {
    render(<VideoAnalytics />);
    await screen.findByRole('table');
    const heading = screen.getByRole('heading', { name: 'By access tier' });
    const panel = heading.parentElement as HTMLElement;
    expect(within(panel).getByRole('heading', { name: 'Free' })).toBeInTheDocument();
    expect(within(panel).getByRole('heading', { name: 'Builder' })).toBeInTheDocument();
    expect(within(panel).getByText('70%')).toBeInTheDocument();
    expect(within(panel).getByText('60%')).toBeInTheDocument();
    expect(within(panel).getByText('30')).toBeInTheDocument();
    expect(within(panel).getByText('21')).toBeInTheDocument();
  });

  it('renders every video in the table with the required columns', async () => {
    render(<VideoAnalytics />);
    await screen.findByRole('table');
    expect(
      within(screen.getByRole('table'))
        .getAllByRole('columnheader')
        .map((h) => (h.textContent ?? '').replace(/[▲▼]/g, ''))
    ).toEqual(['Video', 'Tier', 'Viewers', 'Completed', 'Completion', 'Avg. progress', 'Last watched']);
    expect(tableTitles()).toHaveLength(4);
    const dockerRow = screen.getByRole('rowheader', { name: 'Docker Hardening' }).closest('tr') as HTMLElement;
    expect(within(dockerRow).getByText('Free')).toBeInTheDocument();
    expect(within(dockerRow).getByText('25')).toBeInTheDocument();
    expect(within(dockerRow).getByText('20')).toBeInTheDocument();
    expect(within(dockerRow).getByText('80%')).toBeInTheDocument();
    expect(within(dockerRow).getByText('90%')).toBeInTheDocument();
  });

  it('lists a zero-viewer video with zeros and dashes', async () => {
    render(<VideoAnalytics />);
    await screen.findByRole('table');
    const row = screen.getByRole('rowheader', { name: 'Secrets Management' }).closest('tr') as HTMLElement;
    const cells = within(row).getAllByRole('cell');
    // Tier, Viewers, Completed, Completion, Avg. progress, Last watched
    expect(cells.map((c) => c.textContent)).toEqual(['Builder', '0', '0', '—', '—', '—']);
  });

  it('shows the "As of" time and the footnote', async () => {
    render(<VideoAnalytics />);
    await screen.findByRole('table');
    expect(screen.getByText(/^As of /)).toBeInTheDocument();
    expect(screen.getByText(/Only aggregate numbers are shown/)).toBeInTheDocument();
  });

  it('scrolls the table horizontally on small screens', async () => {
    render(<VideoAnalytics />);
    const table = await screen.findByRole('table');
    expect(table.parentElement).toHaveClass('overflow-x-auto');
  });
});

describe('stale banner', () => {
  it('is hidden when the data is fresh', async () => {
    mockOk(sample({ stale: false }));
    render(<VideoAnalytics />);
    await screen.findByRole('table');
    expect(screen.queryByText(/Showing cached data/)).not.toBeInTheDocument();
  });

  it('is shown when the data is stale', async () => {
    mockOk(sample({ stale: true, generated_at: new Date(Date.now() - 7 * 60000).toISOString() }));
    render(<VideoAnalytics />);
    await screen.findByRole('table');
    expect(screen.getByRole('status')).toHaveTextContent(
      'Showing cached data from 7 minutes ago. A refresh is running.'
    );
  });
});

describe('sorting', () => {
  beforeEach(() => {
    mockOk(sample());
  });

  it('defaults to Viewers descending', async () => {
    render(<VideoAnalytics />);
    await screen.findByRole('table');
    expect(tableTitles()).toEqual([
      'Docker Hardening',
      'Zero Trust Intro',
      'SAST Basics',
      'Secrets Management',
    ]);
    expect(headerCell('Viewers')).toHaveAttribute('aria-sort', 'descending');
  });

  it('renders sort controls as buttons inside scoped column headers', async () => {
    render(<VideoAnalytics />);
    await screen.findByRole('table');
    for (const name of ['Video', 'Tier', 'Viewers', 'Completed', 'Completion', 'Avg. progress', 'Last watched']) {
      const th = headerCell(name);
      expect(th).toHaveAttribute('scope', 'col');
      expect(within(th).getByRole('button', { name })).toBeInTheDocument();
    }
  });

  it('toggles direction when the active column is clicked again', async () => {
    render(<VideoAnalytics />);
    await screen.findByRole('table');
    fireEvent.click(screen.getByRole('button', { name: 'Viewers' }));
    expect(headerCell('Viewers')).toHaveAttribute('aria-sort', 'ascending');
    expect(tableTitles()).toEqual([
      'Secrets Management',
      'SAST Basics',
      'Zero Trust Intro',
      'Docker Hardening',
    ]);
    fireEvent.click(screen.getByRole('button', { name: 'Viewers' }));
    expect(headerCell('Viewers')).toHaveAttribute('aria-sort', 'descending');
  });

  const cases: Array<[string, string[], string[]]> = [
    [
      'Video',
      ['Docker Hardening', 'SAST Basics', 'Secrets Management', 'Zero Trust Intro'],
      ['Zero Trust Intro', 'Secrets Management', 'SAST Basics', 'Docker Hardening'],
    ],
    [
      'Tier',
      ['Secrets Management', 'Zero Trust Intro', 'Docker Hardening', 'SAST Basics'],
      ['Docker Hardening', 'SAST Basics', 'Secrets Management', 'Zero Trust Intro'],
    ],
    [
      'Completed',
      ['Docker Hardening', 'Zero Trust Intro', 'SAST Basics', 'Secrets Management'],
      ['Secrets Management', 'SAST Basics', 'Zero Trust Intro', 'Docker Hardening'],
    ],
    [
      'Completion',
      ['Docker Hardening', 'Zero Trust Intro', 'SAST Basics', 'Secrets Management'],
      ['Secrets Management', 'SAST Basics', 'Zero Trust Intro', 'Docker Hardening'],
    ],
    [
      'Avg. progress',
      ['Docker Hardening', 'Zero Trust Intro', 'SAST Basics', 'Secrets Management'],
      ['Secrets Management', 'SAST Basics', 'Zero Trust Intro', 'Docker Hardening'],
    ],
    [
      'Last watched',
      ['Docker Hardening', 'Zero Trust Intro', 'SAST Basics', 'Secrets Management'],
      // Never-watched videos stay at the bottom in both directions
      ['SAST Basics', 'Zero Trust Intro', 'Docker Hardening', 'Secrets Management'],
    ],
  ];

  it.each(cases)('sorts by %s and sets aria-sort', async (name, first, second) => {
    render(<VideoAnalytics />);
    await screen.findByRole('table');

    fireEvent.click(screen.getByRole('button', { name }));
    const firstDir = name === 'Video' || name === 'Tier' ? 'ascending' : 'descending';
    const secondDir = firstDir === 'ascending' ? 'descending' : 'ascending';
    expect(headerCell(name)).toHaveAttribute('aria-sort', firstDir);
    expect(tableTitles()).toEqual(first);

    fireEvent.click(screen.getByRole('button', { name }));
    expect(headerCell(name)).toHaveAttribute('aria-sort', secondDir);
    expect(tableTitles()).toEqual(second);

    // Only the active column exposes aria-sort
    const sorted = screen
      .getAllByRole('columnheader')
      .filter((th) => th.hasAttribute('aria-sort'));
    expect(sorted).toHaveLength(1);
  });
});

describe('tier filter', () => {
  beforeEach(() => {
    mockOk(sample());
  });

  it('filters the table by Free, Builder and All', async () => {
    render(<VideoAnalytics />);
    await screen.findByRole('table');
    expect(screen.getByRole('button', { name: 'All' })).toHaveAttribute('aria-pressed', 'true');

    fireEvent.click(screen.getByRole('button', { name: 'Free' }));
    expect(screen.getByRole('button', { name: 'Free' })).toHaveAttribute('aria-pressed', 'true');
    expect(tableTitles()).toEqual(['Docker Hardening', 'SAST Basics']);

    fireEvent.click(screen.getByRole('button', { name: 'Builder' }));
    expect(tableTitles()).toEqual(['Zero Trust Intro', 'Secrets Management']);

    fireEvent.click(screen.getByRole('button', { name: 'All' }));
    expect(tableTitles()).toHaveLength(4);
  });

  it('keeps the current sort while filtering', async () => {
    render(<VideoAnalytics />);
    await screen.findByRole('table');
    fireEvent.click(screen.getByRole('button', { name: 'Viewers' })); // ascending
    fireEvent.click(screen.getByRole('button', { name: 'Free' }));
    expect(tableTitles()).toEqual(['SAST Basics', 'Docker Hardening']);
  });

  it('shows a message when a tier has no videos', async () => {
    mockOk(sample({ videos: [DOCKER, SAST], top_videos: [DOCKER, SAST] }));
    render(<VideoAnalytics />);
    await screen.findByRole('table');
    fireEvent.click(screen.getByRole('button', { name: 'Builder' }));
    expect(screen.getByText('No videos in this tier')).toBeInTheDocument();
  });

  it('keeps filter and sort controls at least 44px tall', async () => {
    render(<VideoAnalytics />);
    await screen.findByRole('table');
    expect(screen.getByRole('button', { name: 'Free' })).toHaveClass('min-h-[44px]');
    expect(screen.getByRole('button', { name: 'Viewers' })).toHaveClass('min-h-[44px]');
  });
});

describe('fetching', () => {
  it('fetches exactly once on mount and never polls', async () => {
    jest.useFakeTimers();
    const setIntervalSpy = jest.spyOn(global, 'setInterval');
    mockOk(sample());
    render(<VideoAnalytics />);
    await act(async () => {
      await Promise.resolve();
    });
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(mockApi.getVideoAnalytics).toHaveBeenCalledTimes(1);

    await act(async () => {
      jest.advanceTimersByTime(60 * 60 * 1000);
    });
    expect(mockApi.getVideoAnalytics).toHaveBeenCalledTimes(1);
    expect(setIntervalSpy).not.toHaveBeenCalled();
    setIntervalSpy.mockRestore();
  });

  it('does not refetch when sorting or filtering', async () => {
    mockOk(sample());
    render(<VideoAnalytics />);
    await screen.findByRole('table');
    fireEvent.click(screen.getByRole('button', { name: 'Video' }));
    fireEvent.click(screen.getByRole('button', { name: 'Free' }));
    await waitFor(() => expect(tableTitles()).toHaveLength(2));
    expect(mockApi.getVideoAnalytics).toHaveBeenCalledTimes(1);
  });
});
