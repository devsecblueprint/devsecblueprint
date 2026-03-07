import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { RegistryStatus } from '@/components/admin/RegistryStatus';
import { apiClient } from '@/lib/api';

// Mock the API client
jest.mock('@/lib/api', () => ({
  apiClient: {
    getRegistryStatus: jest.fn(),
  },
}));

// Mock date-fns
jest.mock('date-fns', () => ({
  formatDistanceToNow: jest.fn((date) => '5 minutes ago'),
}));

describe('RegistryStatus Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('displays loading state initially', () => {
    // Mock API to never resolve
    (apiClient.getRegistryStatus as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    );

    render(<RegistryStatus />);

    expect(screen.getByText('Content Registry Status')).toBeInTheDocument();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('displays registry status after successful fetch with healthy status', async () => {
    const mockStatus = {
      schema_version: '1.0.0',
      last_updated: '2024-01-15T08:00:00Z',
      total_entries: 156,
      cache_status: 'loaded' as const,
      cache_ttl_seconds: 300,
      cache_expires_in_seconds: 180,
      s3_bucket: 'devsec-blueprint-content',
      s3_key: 'content-registry/latest.json',
      status: 'healthy' as const,
    };

    (apiClient.getRegistryStatus as jest.Mock).mockResolvedValue({
      data: mockStatus,
      error: null,
    });

    render(<RegistryStatus />);

    await waitFor(() => {
      expect(screen.getByText('healthy')).toBeInTheDocument();
    });

    expect(screen.getByText('1.0.0')).toBeInTheDocument();
    expect(screen.getByText('156')).toBeInTheDocument();
    expect(screen.getByText('Registry is healthy and accessible')).toBeInTheDocument();
  });

  it('displays error state when fetch fails', async () => {
    (apiClient.getRegistryStatus as jest.Mock).mockResolvedValue({
      data: null,
      error: 'Failed to fetch registry status',
    });

    render(<RegistryStatus />);

    await waitFor(() => {
      expect(screen.getByText('Failed to Load Registry Status')).toBeInTheDocument();
    });

    expect(screen.getByText('Failed to fetch registry status')).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
  });

  it('displays unavailable status with error message', async () => {
    const mockStatus = {
      schema_version: null,
      last_updated: null,
      total_entries: 0,
      cache_status: 'error' as const,
      cache_ttl_seconds: null,
      cache_expires_in_seconds: null,
      s3_bucket: 'devsec-blueprint-content',
      s3_key: 'content-registry/latest.json',
      status: 'unavailable' as const,
      error: 'Failed to load registry from S3: NoSuchKey',
    };

    (apiClient.getRegistryStatus as jest.Mock).mockResolvedValue({
      data: mockStatus,
      error: null,
    });

    render(<RegistryStatus />);

    await waitFor(() => {
      expect(screen.getByText('unavailable')).toBeInTheDocument();
    });

    expect(screen.getByText('Registry is unavailable')).toBeInTheDocument();
    expect(screen.getByText('Failed to load registry from S3: NoSuchKey')).toBeInTheDocument();
  });

  it('displays schema version field', async () => {
    const mockStatus = {
      schema_version: '2.1.0',
      last_updated: '2024-01-15T08:00:00Z',
      total_entries: 200,
      cache_status: 'loaded' as const,
      cache_ttl_seconds: 300,
      cache_expires_in_seconds: 180,
      s3_bucket: 'devsec-blueprint-content',
      s3_key: 'content-registry/latest.json',
      status: 'healthy' as const,
    };

    (apiClient.getRegistryStatus as jest.Mock).mockResolvedValue({
      data: mockStatus,
      error: null,
    });

    render(<RegistryStatus />);

    await waitFor(() => {
      expect(screen.getByText('Schema Version')).toBeInTheDocument();
      expect(screen.getByText('2.1.0')).toBeInTheDocument();
    });
  });

  it('displays total entries field', async () => {
    const mockStatus = {
      schema_version: '1.0.0',
      last_updated: '2024-01-15T08:00:00Z',
      total_entries: 250,
      cache_status: 'loaded' as const,
      cache_ttl_seconds: 300,
      cache_expires_in_seconds: 180,
      s3_bucket: 'devsec-blueprint-content',
      s3_key: 'content-registry/latest.json',
      status: 'healthy' as const,
    };

    (apiClient.getRegistryStatus as jest.Mock).mockResolvedValue({
      data: mockStatus,
      error: null,
    });

    render(<RegistryStatus />);

    await waitFor(() => {
      expect(screen.getByText('Total Entries')).toBeInTheDocument();
      expect(screen.getByText('250')).toBeInTheDocument();
    });
  });

  it('displays last updated timestamp as relative time', async () => {
    const mockStatus = {
      schema_version: '1.0.0',
      last_updated: '2024-01-15T08:00:00Z',
      total_entries: 156,
      cache_status: 'loaded' as const,
      cache_ttl_seconds: 300,
      cache_expires_in_seconds: 180,
      s3_bucket: 'devsec-blueprint-content',
      s3_key: 'content-registry/latest.json',
      status: 'healthy' as const,
    };

    (apiClient.getRegistryStatus as jest.Mock).mockResolvedValue({
      data: mockStatus,
      error: null,
    });

    render(<RegistryStatus />);

    await waitFor(() => {
      expect(screen.getByText('Last Updated')).toBeInTheDocument();
      expect(screen.getByText('5 minutes ago')).toBeInTheDocument();
    });
  });

  it('displays cache status indicator', async () => {
    const mockStatus = {
      schema_version: '1.0.0',
      last_updated: '2024-01-15T08:00:00Z',
      total_entries: 156,
      cache_status: 'loaded' as const,
      cache_ttl_seconds: 300,
      cache_expires_in_seconds: 180,
      s3_bucket: 'devsec-blueprint-content',
      s3_key: 'content-registry/latest.json',
      status: 'healthy' as const,
    };

    (apiClient.getRegistryStatus as jest.Mock).mockResolvedValue({
      data: mockStatus,
      error: null,
    });

    render(<RegistryStatus />);

    await waitFor(() => {
      expect(screen.getByText('Cache Status')).toBeInTheDocument();
      expect(screen.getByText('loaded')).toBeInTheDocument();
    });
  });

  it('displays cache expiry countdown', async () => {
    const mockStatus = {
      schema_version: '1.0.0',
      last_updated: '2024-01-15T08:00:00Z',
      total_entries: 156,
      cache_status: 'loaded' as const,
      cache_ttl_seconds: 300,
      cache_expires_in_seconds: 185,
      s3_bucket: 'devsec-blueprint-content',
      s3_key: 'content-registry/latest.json',
      status: 'healthy' as const,
    };

    (apiClient.getRegistryStatus as jest.Mock).mockResolvedValue({
      data: mockStatus,
      error: null,
    });

    render(<RegistryStatus />);

    await waitFor(() => {
      expect(screen.getByText('Expires in 3m 5s')).toBeInTheDocument();
    });
  });

  it('displays S3 location', async () => {
    const mockStatus = {
      schema_version: '1.0.0',
      last_updated: '2024-01-15T08:00:00Z',
      total_entries: 156,
      cache_status: 'loaded' as const,
      cache_ttl_seconds: 300,
      cache_expires_in_seconds: 180,
      s3_bucket: 'test-bucket',
      s3_key: 'registry/test.json',
      status: 'healthy' as const,
    };

    (apiClient.getRegistryStatus as jest.Mock).mockResolvedValue({
      data: mockStatus,
      error: null,
    });

    render(<RegistryStatus />);

    await waitFor(() => {
      expect(screen.getByText('S3 Location')).toBeInTheDocument();
      expect(screen.getByText('s3://test-bucket/registry/test.json')).toBeInTheDocument();
    });
  });

  it('uses green color for healthy status', async () => {
    const mockStatus = {
      schema_version: '1.0.0',
      last_updated: '2024-01-15T08:00:00Z',
      total_entries: 156,
      cache_status: 'loaded' as const,
      cache_ttl_seconds: 300,
      cache_expires_in_seconds: 180,
      s3_bucket: 'devsec-blueprint-content',
      s3_key: 'content-registry/latest.json',
      status: 'healthy' as const,
    };

    (apiClient.getRegistryStatus as jest.Mock).mockResolvedValue({
      data: mockStatus,
      error: null,
    });

    const { container } = render(<RegistryStatus />);

    await waitFor(() => {
      const healthIndicator = container.querySelector('.text-green-600');
      expect(healthIndicator).toBeInTheDocument();
    });
  });

  it('uses red color for unavailable status', async () => {
    const mockStatus = {
      schema_version: null,
      last_updated: null,
      total_entries: 0,
      cache_status: 'error' as const,
      cache_ttl_seconds: null,
      cache_expires_in_seconds: null,
      s3_bucket: 'devsec-blueprint-content',
      s3_key: 'content-registry/latest.json',
      status: 'unavailable' as const,
      error: 'Failed to load registry',
    };

    (apiClient.getRegistryStatus as jest.Mock).mockResolvedValue({
      data: mockStatus,
      error: null,
    });

    const { container } = render(<RegistryStatus />);

    await waitFor(() => {
      const healthIndicator = container.querySelector('.text-red-600');
      expect(healthIndicator).toBeInTheDocument();
    });
  });

  it('auto-refreshes every 60 seconds', async () => {
    const mockStatus = {
      schema_version: '1.0.0',
      last_updated: '2024-01-15T08:00:00Z',
      total_entries: 156,
      cache_status: 'loaded' as const,
      cache_ttl_seconds: 300,
      cache_expires_in_seconds: 180,
      s3_bucket: 'devsec-blueprint-content',
      s3_key: 'content-registry/latest.json',
      status: 'healthy' as const,
    };

    (apiClient.getRegistryStatus as jest.Mock).mockResolvedValue({
      data: mockStatus,
      error: null,
    });

    render(<RegistryStatus />);

    // Initial fetch
    await waitFor(() => {
      expect(apiClient.getRegistryStatus).toHaveBeenCalledTimes(1);
    });

    // Fast-forward 60 seconds
    jest.advanceTimersByTime(60000);

    // Should have fetched again
    await waitFor(() => {
      expect(apiClient.getRegistryStatus).toHaveBeenCalledTimes(2);
    });
  });

  it('displays N/A for null schema version', async () => {
    const mockStatus = {
      schema_version: null,
      last_updated: '2024-01-15T08:00:00Z',
      total_entries: 156,
      cache_status: 'loaded' as const,
      cache_ttl_seconds: 300,
      cache_expires_in_seconds: 180,
      s3_bucket: 'devsec-blueprint-content',
      s3_key: 'content-registry/latest.json',
      status: 'healthy' as const,
    };

    (apiClient.getRegistryStatus as jest.Mock).mockResolvedValue({
      data: mockStatus,
      error: null,
    });

    render(<RegistryStatus />);

    await waitFor(() => {
      expect(screen.getByText('Schema Version')).toBeInTheDocument();
      expect(screen.getByText('N/A')).toBeInTheDocument();
    });
  });

  it('displays N/A for null last updated', async () => {
    const mockStatus = {
      schema_version: '1.0.0',
      last_updated: null,
      total_entries: 156,
      cache_status: 'loaded' as const,
      cache_ttl_seconds: 300,
      cache_expires_in_seconds: 180,
      s3_bucket: 'devsec-blueprint-content',
      s3_key: 'content-registry/latest.json',
      status: 'healthy' as const,
    };

    (apiClient.getRegistryStatus as jest.Mock).mockResolvedValue({
      data: mockStatus,
      error: null,
    });

    render(<RegistryStatus />);

    await waitFor(() => {
      expect(screen.getByText('Last Updated')).toBeInTheDocument();
      expect(screen.getAllByText('N/A').length).toBeGreaterThan(0);
    });
  });
});
