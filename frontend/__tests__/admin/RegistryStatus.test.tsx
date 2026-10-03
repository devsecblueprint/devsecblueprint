/**
 * Unit tests for admin RegistryStatus.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { RegistryStatus } from '@/components/admin/RegistryStatus';

jest.mock('@/lib/api', () => ({ apiClient: { getRegistryStatus: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function healthy(overrides: Record<string, unknown> = {}) {
  return {
    schema_version: '1.0.0',
    last_updated: '2026-01-01T00:00:00Z',
    total_entries: 150,
    cache_status: 'loaded',
    cache_ttl_seconds: 300,
    cache_expires_in_seconds: 120,
    s3_bucket: 'my-bucket',
    s3_key: 'registry.json',
    status: 'healthy',
    ...overrides,
  };
}

afterEach(() => {
  jest.useRealTimers();
});

it('shows healthy status with key metrics', async () => {
  mockApi.getRegistryStatus.mockResolvedValue({ data: healthy() as never, statusCode: 200 });
  render(<RegistryStatus />);
  expect(await screen.findByText(/Registry is healthy and accessible/i)).toBeInTheDocument();
  expect(screen.getByText('1.0.0')).toBeInTheDocument();
  expect(screen.getByText('150')).toBeInTheDocument();
  expect(screen.getByText('s3://my-bucket/registry.json')).toBeInTheDocument();
});

it('shows unavailable status with an error message', async () => {
  mockApi.getRegistryStatus.mockResolvedValue({
    data: healthy({ status: 'unavailable', error: 'S3 timeout', cache_status: 'error' }) as never,
    statusCode: 200,
  });
  render(<RegistryStatus />);
  expect(await screen.findByText(/Registry is unavailable/i)).toBeInTheDocument();
  expect(screen.getByText('S3 timeout')).toBeInTheDocument();
});

it('shows an error state with retry', async () => {
  mockApi.getRegistryStatus.mockResolvedValue({ error: 'boom', statusCode: 500 });
  render(<RegistryStatus />);
  expect(await screen.findByText('Failed to Load Registry Status')).toBeInTheDocument();
  mockApi.getRegistryStatus.mockResolvedValue({ data: healthy() as never, statusCode: 200 });
  fireEvent.click(screen.getByRole('button', { name: /try again/i }));
  expect(await screen.findByText(/Registry is healthy/i)).toBeInTheDocument();
});

it('renders cache status and expiry details', async () => {
  mockApi.getRegistryStatus.mockResolvedValue({ data: healthy() as never, statusCode: 200 });
  render(<RegistryStatus />);
  await screen.findByText(/Registry is healthy/i);
  // cache_status 'loaded' -> "loaded" label; expires in 2m 0s (120s)
  expect(screen.getByText('loaded')).toBeInTheDocument();
  expect(screen.getByText(/Expires in 2m 0s/i)).toBeInTheDocument();
});
