/**
 * Unit tests for PathwayManagement.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { PathwayManagement } from '@/app/admin/components/certifications/PathwayManagement';

jest.mock('@/lib/api', () => ({ apiClient: { get: jest.fn(), put: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function pathway(id: string, overrides: Record<string, unknown> = {}) {
  return {
    pathway_id: id,
    pathway_code: 'DSE',
    display_name: `Pathway ${id}`,
    current_version: '2026.1',
    is_active: true,
    ...overrides,
  };
}

beforeEach(() => jest.clearAllMocks());

it('renders pathways after loading', async () => {
  mockApi.get.mockResolvedValue({ data: [pathway('p1')] as never, statusCode: 200 });
  render(<PathwayManagement />);
  expect(await screen.findByText('Pathway p1')).toBeInTheDocument();
  expect(screen.getByText('Version: 2026.1')).toBeInTheDocument();
});

it('shows empty state when no pathways exist', async () => {
  mockApi.get.mockResolvedValue({ data: [] as never, statusCode: 200 });
  render(<PathwayManagement />);
  expect(await screen.findByText(/No pathways defined yet/i)).toBeInTheDocument();
});

it('shows error state with retry', async () => {
  mockApi.get.mockResolvedValue({ error: 'boom', statusCode: 500 });
  render(<PathwayManagement />);
  expect(await screen.findByText('Failed to Load Pathways')).toBeInTheDocument();
  mockApi.get.mockResolvedValue({ data: [pathway('p1')] as never, statusCode: 200 });
  fireEvent.click(screen.getByRole('button', { name: /try again/i }));
  expect(await screen.findByText('Pathway p1')).toBeInTheDocument();
});

it('opens the create-version form and gates submit on required fields', async () => {
  mockApi.get.mockResolvedValue({ data: [pathway('p1')] as never, statusCode: 200 });
  render(<PathwayManagement />);
  await screen.findByText('Pathway p1');

  fireEvent.click(screen.getByRole('button', { name: /create new version for Pathway p1/i }));
  expect(screen.getByText('Create New Version')).toBeInTheDocument();

  const submit = screen.getByRole('button', { name: /^create version$/i });
  expect(submit).toBeDisabled();

  fireEvent.change(screen.getByLabelText(/^Version$/i), { target: { value: '2027.1' } });
  fireEvent.change(screen.getByLabelText(/Display Name/i), { target: { value: 'New Pathway' } });
  expect(submit).toBeEnabled();
});

it('submits a new version with parsed learning requirements', async () => {
  mockApi.get.mockResolvedValue({ data: [pathway('p1')] as never, statusCode: 200 });
  mockApi.put.mockResolvedValue({ data: {} as never, statusCode: 200 });
  render(<PathwayManagement />);
  await screen.findByText('Pathway p1');

  fireEvent.click(screen.getByRole('button', { name: /create new version for Pathway p1/i }));
  fireEvent.change(screen.getByLabelText(/^Version$/i), { target: { value: '2027.1' } });
  fireEvent.change(screen.getByLabelText(/Display Name/i), { target: { value: 'New Pathway' } });
  fireEvent.change(screen.getByLabelText(/Learning Requirements/i), { target: { value: 'a, b , c' } });
  fireEvent.click(screen.getByRole('button', { name: /^create version$/i }));

  await waitFor(() => expect(mockApi.put).toHaveBeenCalled());
  const [, body] = mockApi.put.mock.calls[0] as [string, Record<string, unknown>];
  expect(body.version).toBe('2027.1');
  expect(body.learning_requirements).toEqual(['a', 'b', 'c']);
});

it('toggles version history and fetches it', async () => {
  mockApi.get
    .mockResolvedValueOnce({ data: [pathway('p1')] as never, statusCode: 200 })
    .mockResolvedValueOnce({
      data: [{ pathway_id: 'p1', version: '2026.1', display_name: 'Pathway p1', is_active: true, created_at: '2026-01-01' }] as never,
      statusCode: 200,
    });
  render(<PathwayManagement />);
  await screen.findByText('Pathway p1');

  fireEvent.click(screen.getByRole('button', { name: /toggle version history for Pathway p1/i }));
  expect(await screen.findByText('Version History')).toBeInTheDocument();
  expect(await screen.findByText('v2026.1')).toBeInTheDocument();
});
