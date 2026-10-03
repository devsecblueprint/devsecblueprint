/**
 * Unit tests for admin ExportData.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { ExportData } from '@/components/admin/ExportData';

jest.mock('@/lib/api', () => ({ apiClient: { exportUsers: jest.fn(), exportCapstoneSubmissions: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

beforeEach(() => jest.clearAllMocks());

it('renders both export options', () => {
  render(<ExportData />);
  expect(screen.getByText('Export All Users')).toBeInTheDocument();
  expect(screen.getByText('Export Capstone Submissions')).toBeInTheDocument();
});

it('exports users', async () => {
  mockApi.exportUsers.mockResolvedValue(undefined);
  render(<ExportData />);
  fireEvent.click(screen.getByRole('button', { name: /export users/i }));
  await waitFor(() => expect(mockApi.exportUsers).toHaveBeenCalled());
});

it('exports capstone submissions', async () => {
  mockApi.exportCapstoneSubmissions.mockResolvedValue(undefined);
  render(<ExportData />);
  fireEvent.click(screen.getByRole('button', { name: /export submissions/i }));
  await waitFor(() => expect(mockApi.exportCapstoneSubmissions).toHaveBeenCalled());
});

it('swallows export errors without crashing', async () => {
  mockApi.exportUsers.mockRejectedValue(new Error('fail'));
  const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
  render(<ExportData />);
  fireEvent.click(screen.getByRole('button', { name: /export users/i }));
  await waitFor(() => expect(spy).toHaveBeenCalled());
  // Button returns to its normal label afterward
  expect(await screen.findByRole('button', { name: /export users/i })).toBeInTheDocument();
  spy.mockRestore();
});
