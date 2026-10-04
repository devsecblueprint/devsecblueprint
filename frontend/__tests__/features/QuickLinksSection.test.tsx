/**
 * Unit tests for QuickLinksSection.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { QuickLinksSection } from '@/components/features/QuickLinksSection';

const replaceMock = jest.fn();
let searchParamsValue = new URLSearchParams();
jest.mock('next/navigation', () => ({
  useRouter: () => ({ replace: replaceMock }),
  useSearchParams: () => searchParamsValue,
}));
jest.mock('@/lib/api', () => ({ apiClient: { get: jest.fn(), post: jest.fn(), delete: jest.fn() } }));
jest.mock('@/components/features/TestimonialForm', () => ({
  TestimonialForm: ({ isOpen }: { isOpen: boolean }) => (isOpen ? <div data-testid="testimonial-modal" /> : null),
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

beforeEach(() => {
  jest.clearAllMocks();
  searchParamsValue = new URLSearchParams();
  mockApi.get.mockResolvedValue({ data: { connected: false } as never, statusCode: 200 });
});

it('renders the community engagement cards', async () => {
  render(<QuickLinksSection />);
  expect(screen.getByText('Community & Engagement')).toBeInTheDocument();
  expect(screen.getByText('Star on GitHub')).toBeInTheDocument();
  expect(screen.getByText('Merch Store')).toBeInTheDocument();
});

it('shows "Connect Discord" when not connected', async () => {
  render(<QuickLinksSection />);
  expect(await screen.findByText('Connect Discord')).toBeInTheDocument();
});

it('shows "Discord Connected" when connected', async () => {
  mockApi.get.mockResolvedValue({ data: { connected: true, discord_username: 'ada' } as never, statusCode: 200 });
  render(<QuickLinksSection />);
  expect(await screen.findByText('Discord Connected')).toBeInTheDocument();
});

it('opens the testimonial modal from the success-story card', async () => {
  render(<QuickLinksSection />);
  fireEvent.click(screen.getByLabelText(/share your success story/i));
  expect(screen.getByTestId('testimonial-modal')).toBeInTheDocument();
});

it('shows the confirm modal when ?discord=pending is present', async () => {
  searchParamsValue = new URLSearchParams('discord=pending');
  mockApi.get.mockResolvedValue({ data: { connected: false, discord_username: 'ada' } as never, statusCode: 200 });
  render(<QuickLinksSection />);
  expect(await screen.findByText('Confirm Discord Account')).toBeInTheDocument();
});

it('confirms the Discord identity and redirects', async () => {
  searchParamsValue = new URLSearchParams('discord=pending');
  mockApi.get.mockResolvedValue({ data: { connected: false, discord_username: 'ada' } as never, statusCode: 200 });
  mockApi.post.mockResolvedValue({ data: {} as never, statusCode: 200 });
  render(<QuickLinksSection />);
  fireEvent.click(await screen.findByRole('button', { name: /yes, this is my account/i }));
  await waitFor(() => expect(mockApi.post).toHaveBeenCalledWith('/api/discord/confirm', {}));
  await waitFor(() => expect(replaceMock).toHaveBeenCalledWith('/dashboard'));
});

it('disconnects when choosing another account', async () => {
  searchParamsValue = new URLSearchParams('discord=pending');
  mockApi.get.mockResolvedValue({ data: { connected: false, discord_username: 'ada' } as never, statusCode: 200 });
  mockApi.delete.mockResolvedValue({ data: { message: 'ok' }, statusCode: 200 });
  render(<QuickLinksSection />);
  fireEvent.click(await screen.findByRole('button', { name: /disconnect & choose another/i }));
  await waitFor(() => expect(mockApi.delete).toHaveBeenCalledWith('/api/discord/disconnect'));
});
