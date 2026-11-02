/**
 * Unit tests for BroadcastModal.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { BroadcastModal, stripMarkdown } from '@/components/BroadcastModal';

jest.mock('@/lib/api', () => ({
  apiClient: { dismissBroadcast: jest.fn(), dismissAllBroadcasts: jest.fn() },
}));
jest.mock('@/components/MarkdownRenderer', () => ({
  __esModule: true,
  default: ({ markdown }: { markdown: string }) => <div data-testid="md">{markdown}</div>,
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function broadcast(id: string, overrides: Record<string, unknown> = {}) {
  return {
    broadcast_id: id,
    title: `Title ${id}`,
    message: `Message body for ${id}`,
    link: '',
    created_by: 'admin',
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  mockApi.dismissBroadcast.mockResolvedValue({ data: { message: 'ok' }, statusCode: 200 });
  mockApi.dismissAllBroadcasts.mockResolvedValue({ data: { message: 'ok' }, statusCode: 200 });
});

it('renders the first broadcast title and date', () => {
  render(<BroadcastModal broadcasts={[broadcast('1')]} onAllDismissed={jest.fn()} />);
  expect(screen.getByText('Title 1')).toBeInTheDocument();
});

it('renders nothing when there are no broadcasts', () => {
  const { container } = render(<BroadcastModal broadcasts={[]} onAllDismissed={jest.fn()} />);
  expect(container.querySelector('[role="dialog"]')).toBeNull();
});

it('shows the counter and navigates between multiple broadcasts', () => {
  render(<BroadcastModal broadcasts={[broadcast('1'), broadcast('2')]} onAllDismissed={jest.fn()} />);
  expect(screen.getByText('1 of 2')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /next/i }));
  expect(screen.getByText('Title 2')).toBeInTheDocument();
  expect(screen.getByText('2 of 2')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /previous/i }));
  expect(screen.getByText('Title 1')).toBeInTheDocument();
});

it('expands long content with Read More and collapses with Show Less', () => {
  const longMsg = 'x'.repeat(200);
  render(<BroadcastModal broadcasts={[broadcast('1', { message: longMsg })]} onAllDismissed={jest.fn()} />);
  expect(screen.getByRole('button', { name: /read more/i })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /read more/i }));
  expect(screen.getByTestId('md')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /show less/i })).toBeInTheDocument();
});

it('dismisses the current broadcast and advances', async () => {
  const onAllDismissed = jest.fn();
  render(<BroadcastModal broadcasts={[broadcast('1'), broadcast('2')]} onAllDismissed={onAllDismissed} />);
  fireEvent.click(screen.getByRole('button', { name: /got it/i }));
  await waitFor(() => expect(mockApi.dismissBroadcast).toHaveBeenCalledWith('1'));
  // Second broadcast now shown; not all dismissed yet
  expect(await screen.findByText('Title 2')).toBeInTheDocument();
  expect(onAllDismissed).not.toHaveBeenCalled();
});

it('calls onAllDismissed after dismissing the last broadcast', async () => {
  const onAllDismissed = jest.fn();
  render(<BroadcastModal broadcasts={[broadcast('1')]} onAllDismissed={onAllDismissed} />);
  fireEvent.click(screen.getByRole('button', { name: /got it/i }));
  await waitFor(() => expect(onAllDismissed).toHaveBeenCalled());
});

it('dismisses all broadcasts at once', async () => {
  const onAllDismissed = jest.fn();
  render(<BroadcastModal broadcasts={[broadcast('1'), broadcast('2')]} onAllDismissed={onAllDismissed} />);
  fireEvent.click(screen.getByRole('button', { name: /dismiss all/i }));
  await waitFor(() => expect(mockApi.dismissAllBroadcasts).toHaveBeenCalled());
  expect(onAllDismissed).toHaveBeenCalled();
});

it('keeps the modal open if dismiss-all fails', async () => {
  const onAllDismissed = jest.fn();
  mockApi.dismissAllBroadcasts.mockResolvedValue({ error: 'network', statusCode: 500 });
  const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
  render(<BroadcastModal broadcasts={[broadcast('1'), broadcast('2')]} onAllDismissed={onAllDismissed} />);
  fireEvent.click(screen.getByRole('button', { name: /dismiss all/i }));
  await waitFor(() => expect(mockApi.dismissAllBroadcasts).toHaveBeenCalled());
  expect(onAllDismissed).not.toHaveBeenCalled();
  spy.mockRestore();
});

it('dismiss-all only calls dismiss-all, not the per-broadcast dismiss', async () => {
  // Regression guard: the Dismiss All click must not also bubble to the
  // backdrop's dismiss-current handler. If it did, dismissBroadcast would
  // fire alongside dismissAllBroadcasts.
  const onAllDismissed = jest.fn();
  render(<BroadcastModal broadcasts={[broadcast('1'), broadcast('2')]} onAllDismissed={onAllDismissed} />);
  fireEvent.click(screen.getByRole('button', { name: /dismiss all/i }));
  await waitFor(() => expect(mockApi.dismissAllBroadcasts).toHaveBeenCalledTimes(1));
  expect(mockApi.dismissBroadcast).not.toHaveBeenCalled();
  expect(onAllDismissed).toHaveBeenCalledTimes(1);
});

it('action buttons are type="button" so they never act as implicit submits', () => {
  render(<BroadcastModal broadcasts={[broadcast('1'), broadcast('2')]} onAllDismissed={jest.fn()} />);
  expect(screen.getByRole('button', { name: /dismiss all/i })).toHaveAttribute('type', 'button');
  expect(screen.getByRole('button', { name: /got it/i })).toHaveAttribute('type', 'button');
});

it('renders a CTA link when provided', () => {
  render(<BroadcastModal broadcasts={[broadcast('1', { link: 'https://example.com' })]} onAllDismissed={jest.fn()} />);
  const cta = screen.getByRole('link', { name: /check it out/i });
  expect(cta).toHaveAttribute('href', 'https://example.com');
  expect(cta).toHaveAttribute('target', '_blank');
});


describe('collapsed preview shows plain text, not markdown syntax', () => {
  const announcement =
    '**Your next hands-on walkthrough is here.**\n\n**Connect Authentik to Google Cloud**\n\n' +
    'Connect Authentik using SAML 2.0.\n\n**Level:** Intermediate  \n**Estimated time:** 1 hr\n\n' +
    'Ready to put it into practice?';

  it('removes the bold markers from the opening line', () => {
    render(<BroadcastModal broadcasts={[broadcast('1', { message: announcement })]} onAllDismissed={jest.fn()} />);
    expect(screen.getByText('Your next hands-on walkthrough is here.')).toBeInTheDocument();
    expect(screen.queryByText(/\*\*/)).toBeNull();
    // Only the first paragraph is previewed; the rest waits behind Read More
    expect(screen.queryByText(/Ready to put it into practice/)).toBeNull();
    expect(screen.getByRole('button', { name: /read more/i })).toBeInTheDocument();
  });

  it('still renders the full markdown body when expanded', () => {
    render(<BroadcastModal broadcasts={[broadcast('1', { message: announcement })]} onAllDismissed={jest.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /read more/i }));
    expect(screen.getByTestId('md').textContent).toBe(announcement);
  });
});

describe('stripMarkdown', () => {
  it.each([
    ['**bold**', 'bold'],
    ['__bold__', 'bold'],
    ['a **bold** and *italic* word', 'a bold and italic word'],
    ['an _italic_ word', 'an italic word'],
    ['keep snake_case_names intact', 'keep snake_case_names intact'],
    ['2 * 3 * 4 stays', '2 * 3 * 4 stays'],
    ['[a link](https://x.test/path)', 'a link'],
    ['![diagram](https://x.test/i.png) caption', 'diagram caption'],
    ['# Heading', 'Heading'],
    ['  ### Sub heading', 'Sub heading'],
    ['run `kubectl apply` now', 'run kubectl apply now'],
    ['Terraform\\_Cloud \\*Guide\\*', 'Terraform_Cloud *Guide*'],
    ['line one  \nline two', 'line one\nline two'],
    ['plain text', 'plain text'],
    ['', ''],
  ])('%j -> %j', (input, expected) => {
    expect(stripMarkdown(input)).toBe(expected);
  });

  it('does not run away on pathological input', () => {
    const nasty = '*'.repeat(5000) + '_'.repeat(5000) + '['.repeat(2000);
    const start = Date.now();
    stripMarkdown(nasty);
    expect(Date.now() - start).toBeLessThan(500);
  });
});
