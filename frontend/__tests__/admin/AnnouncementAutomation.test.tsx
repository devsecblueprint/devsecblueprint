/**
 * Tests for the Automation tab (AnnouncementAutomation).
 */
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { AnnouncementAutomation } from '@/components/admin/AnnouncementAutomation';

jest.mock('@/lib/api', () => ({
  apiClient: {
    getAnnouncements: jest.fn(),
    retryAnnouncement: jest.fn(),
    baselineAnnouncements: jest.fn(),
  },
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

const record = (overrides: Record<string, unknown> = {}) => ({
  content_key: 'VIDEO#v1',
  content_type: 'video',
  content_id: 'v1',
  title: 'Video One',
  status: 'SENT',
  first_seen_at: '2026-01-01T00:00:00Z',
  sent_at: '2026-01-01T00:05:00Z',
  attempts: 1,
  last_error: null,
  ...overrides,
});

function respond(enabled: boolean, announcements: unknown[], failed = 0) {
  return {
    data: { enabled, failed_count: failed, announcements } as never,
    statusCode: 200,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
});

it('shows a loading spinner then the empty state', async () => {
  mockApi.getAnnouncements.mockResolvedValue(respond(true, []));
  render(<AnnouncementAutomation />);
  expect(await screen.findByText('No announcements yet')).toBeInTheDocument();
});

it('shows the Enabled pill without the deployment note', async () => {
  mockApi.getAnnouncements.mockResolvedValue(respond(true, []));
  render(<AnnouncementAutomation />);
  expect(await screen.findByText('Enabled')).toBeInTheDocument();
  expect(screen.queryByText(/ANNOUNCEMENTS_ENABLED/)).not.toBeInTheDocument();
});

it('shows the Disabled pill and the deployment configuration note', async () => {
  mockApi.getAnnouncements.mockResolvedValue(respond(false, []));
  render(<AnnouncementAutomation />);
  expect(await screen.findByText('Disabled')).toBeInTheDocument();
  expect(screen.getByText(/ANNOUNCEMENTS_ENABLED/)).toBeInTheDocument();
  expect(screen.getByText(/deployment configuration/i)).toBeInTheDocument();
});

it('renders record columns', async () => {
  mockApi.getAnnouncements.mockResolvedValue(
    respond(true, [record({ content_key: 'WALKTHROUGH#w', content_type: 'walkthrough', title: 'Walk', status: 'FAILED', attempts: 3, last_error: 'SES down', sent_at: null })], 1),
  );
  render(<AnnouncementAutomation />);
  const row = (await screen.findByText('Walk')).closest('tr') as HTMLElement;
  expect(within(row).getByText('walkthrough')).toBeInTheDocument();
  expect(within(row).getByText('FAILED')).toBeInTheDocument();
  expect(within(row).getByText('3')).toBeInTheDocument();
  expect(within(row).getByText('SES down')).toBeInTheDocument();
});

it('shows an error with Try Again that reloads', async () => {
  mockApi.getAnnouncements.mockResolvedValueOnce({ error: 'nope', statusCode: 500 });
  render(<AnnouncementAutomation />);
  expect(await screen.findByText('nope')).toBeInTheDocument();
  mockApi.getAnnouncements.mockResolvedValueOnce(respond(true, [record()]));
  fireEvent.click(screen.getByRole('button', { name: /try again/i }));
  expect(await screen.findByText('Video One')).toBeInTheDocument();
});

describe('Retry', () => {
  const rows = [
    record({ content_key: 'VIDEO#sent', title: 'Sent one', status: 'SENT' }),
    record({ content_key: 'VIDEO#failed', title: 'Failed one', status: 'FAILED', last_error: 'x' }),
    record({ content_key: 'WALKTHROUGH#pending', content_type: 'walkthrough', title: 'Pending one', status: 'PENDING' }),
    record({ content_key: 'WALKTHROUGH#base', content_type: 'walkthrough', title: 'Base one', status: 'BASELINED' }),
  ];

  it('is only shown on FAILED rows', async () => {
    mockApi.getAnnouncements.mockResolvedValue(respond(true, rows, 1));
    render(<AnnouncementAutomation />);
    await screen.findByText('Failed one');
    const retryButtons = screen.getAllByRole('button', { name: /^retry/i });
    expect(retryButtons).toHaveLength(1);
    expect(within(screen.getByText('Failed one').closest('tr') as HTMLElement).getByRole('button', { name: /retry/i })).toBe(retryButtons[0]);
  });

  it('calls the API with the content key and refreshes the list', async () => {
    mockApi.getAnnouncements.mockResolvedValueOnce(respond(true, rows, 1));
    mockApi.retryAnnouncement.mockResolvedValue({ data: { message: 'Retry queued' }, statusCode: 200 });
    mockApi.getAnnouncements.mockResolvedValueOnce(respond(true, rows.map((r) => (r.status === 'FAILED' ? { ...r, status: 'SENT' } : r)), 0));
    render(<AnnouncementAutomation />);
    await screen.findByText('Failed one');
    fireEvent.click(screen.getByRole('button', { name: /retry failed one/i }));
    await waitFor(() => expect(mockApi.retryAnnouncement).toHaveBeenCalledWith('VIDEO#failed'));
    expect(await screen.findByText('Retry queued')).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByRole('button', { name: /^retry/i })).not.toBeInTheDocument());
    expect(mockApi.getAnnouncements).toHaveBeenCalledTimes(2);
  });

  it('shows the error when the retry fails', async () => {
    mockApi.getAnnouncements.mockResolvedValue(respond(true, rows, 1));
    mockApi.retryAnnouncement.mockResolvedValue({ error: 'Announcement is not FAILED', statusCode: 409 });
    render(<AnnouncementAutomation />);
    await screen.findByText('Failed one');
    fireEvent.click(screen.getByRole('button', { name: /retry failed one/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Announcement is not FAILED');
  });
});

describe('Baseline walkthroughs', () => {
  it('does not call the API until the confirmation dialog is confirmed', async () => {
    mockApi.getAnnouncements.mockResolvedValue(respond(true, []));
    mockApi.baselineAnnouncements.mockResolvedValue({ data: { message: 'Baselined 12 walkthroughs', baselined: 12 }, statusCode: 200 });
    render(<AnnouncementAutomation />);
    await screen.findByText('No announcements yet');

    fireEvent.click(screen.getByRole('button', { name: /baseline walkthroughs/i }));
    const dialog = screen.getByRole('dialog');
    expect(within(dialog).getByText(/marked as already announced/i)).toBeInTheDocument();
    expect(mockApi.baselineAnnouncements).not.toHaveBeenCalled();

    fireEvent.click(within(dialog).getByRole('button', { name: /confirm baseline/i }));
    await waitFor(() => expect(mockApi.baselineAnnouncements).toHaveBeenCalledTimes(1));
    expect(await screen.findByText('Baselined 12 walkthroughs')).toBeInTheDocument();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('cancelling closes the dialog without calling the API', async () => {
    mockApi.getAnnouncements.mockResolvedValue(respond(true, []));
    render(<AnnouncementAutomation />);
    await screen.findByText('No announcements yet');
    fireEvent.click(screen.getByRole('button', { name: /baseline walkthroughs/i }));
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: /cancel/i }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(mockApi.baselineAnnouncements).not.toHaveBeenCalled();
  });

  it('Escape closes the dialog without calling the API', async () => {
    mockApi.getAnnouncements.mockResolvedValue(respond(true, []));
    render(<AnnouncementAutomation />);
    await screen.findByText('No announcements yet');
    fireEvent.click(screen.getByRole('button', { name: /baseline walkthroughs/i }));
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(mockApi.baselineAnnouncements).not.toHaveBeenCalled();
  });

  it('surfaces a baseline error', async () => {
    mockApi.getAnnouncements.mockResolvedValue(respond(true, []));
    mockApi.baselineAnnouncements.mockResolvedValue({ error: 'registry empty', statusCode: 500 });
    render(<AnnouncementAutomation />);
    await screen.findByText('No announcements yet');
    fireEvent.click(screen.getByRole('button', { name: /baseline walkthroughs/i }));
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: /confirm baseline/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent('registry empty');
  });
});
