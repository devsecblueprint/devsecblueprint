/**
 * Unit tests for WalkthroughPreviewModal.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { WalkthroughPreviewModal } from '@/components/dashboard/WalkthroughPreviewModal';

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href, onClick }: { children: React.ReactNode; href: string; onClick?: () => void }) => (
    <a href={href} onClick={onClick}>{children}</a>
  ),
}));
jest.mock('@/lib/api', () => ({
  apiClient: { resetWalkthroughProgress: jest.fn(), updateWalkthroughProgress: jest.fn() },
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function wt(status: string, overrides: Record<string, unknown> = {}) {
  return {
    id: 'wt-1',
    title: 'AWS Lab',
    description: 'desc',
    difficulty: 'Beginner',
    estimatedTime: 30,
    topics: ['aws'],
    prerequisites: ['Basic AWS'],
    progress: { status },
    ...overrides,
  };
}

function renderModal(status = 'not_started', props: Partial<React.ComponentProps<typeof WalkthroughPreviewModal>> = {}) {
  const onClose = props.onClose ?? jest.fn();
  const onProgressReset = props.onProgressReset ?? jest.fn();
  render(
    <WalkthroughPreviewModal walkthrough={wt(status) as never} isOpen onClose={onClose} onProgressReset={onProgressReset} />,
  );
  return { onClose, onProgressReset };
}

beforeEach(() => jest.clearAllMocks());

it('renders nothing when closed', () => {
  const { container } = render(
    <WalkthroughPreviewModal walkthrough={wt('not_started') as never} isOpen={false} onClose={jest.fn()} />,
  );
  expect(container).toBeEmptyDOMElement();
});

it('renders title, topics, and prerequisites', () => {
  renderModal();
  expect(screen.getByText('AWS Lab')).toBeInTheDocument();
  expect(screen.getByText('aws')).toBeInTheDocument();
  expect(screen.getByText('Basic AWS')).toBeInTheDocument();
});

it('shows "Start Walkthrough" for a not-started walkthrough', () => {
  renderModal('not_started');
  expect(screen.getByRole('link', { name: /start walkthrough/i })).toBeInTheDocument();
});

it('shows "Continue" and a reset button for an in-progress walkthrough', () => {
  renderModal('in_progress');
  expect(screen.getByRole('link', { name: /continue/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /reset progress/i })).toBeInTheDocument();
});

it('marks progress in_progress when starting a not-started walkthrough', async () => {
  mockApi.updateWalkthroughProgress.mockResolvedValue({ data: { message: 'ok' }, statusCode: 200 });
  renderModal('not_started');
  fireEvent.click(screen.getByRole('link', { name: /start walkthrough/i }));
  await waitFor(() => expect(mockApi.updateWalkthroughProgress).toHaveBeenCalledWith('wt-1', 'in_progress'));
});

it('resets progress after confirmation', async () => {
  mockApi.resetWalkthroughProgress.mockResolvedValue({ data: { message: 'ok' } as never, statusCode: 200 });
  const { onProgressReset } = renderModal('completed');
  fireEvent.click(screen.getByRole('button', { name: /reset progress/i }));
  fireEvent.click(screen.getByRole('button', { name: /yes, reset/i }));
  await waitFor(() => expect(mockApi.resetWalkthroughProgress).toHaveBeenCalledWith('wt-1'));
  expect(onProgressReset).toHaveBeenCalled();
});

it('cancels the reset confirmation', () => {
  renderModal('completed');
  fireEvent.click(screen.getByRole('button', { name: /reset progress/i }));
  fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
  expect(screen.getByRole('button', { name: /reset progress/i })).toBeInTheDocument();
});

it('closes via the close button', () => {
  const { onClose } = renderModal();
  fireEvent.click(screen.getByLabelText('Close preview'));
  expect(onClose).toHaveBeenCalled();
});
