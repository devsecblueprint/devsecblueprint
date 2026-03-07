import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { CapstoneSubmissions } from '@/components/admin/CapstoneSubmissions';
import { apiClient } from '@/lib/api';

// Mock the API client
jest.mock('@/lib/api', () => ({
  apiClient: {
    getCapstoneSubmissions: jest.fn(),
  },
}));

// Mock date-fns
jest.mock('date-fns', () => ({
  formatDistanceToNow: jest.fn((date) => '2 hours ago'),
}));

describe('CapstoneSubmissions Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('displays loading state initially', () => {
    // Mock API to never resolve
    (apiClient.getCapstoneSubmissions as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    );

    render(<CapstoneSubmissions />);

    expect(screen.getByText('Capstone Submissions')).toBeInTheDocument();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('displays submissions after successful fetch', async () => {
    const mockSubmissions = {
      submissions: [
        {
          user_id: 'github|12345678',
          github_username: 'testuser',
          repo_url: 'https://github.com/testuser/capstone-project',
          submitted_at: '2024-01-15T10:30:00Z',
          updated_at: '2024-01-15T10:30:00Z',
        },
      ],
      total_count: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };

    (apiClient.getCapstoneSubmissions as jest.Mock).mockResolvedValue({
      data: mockSubmissions,
      error: null,
    });

    render(<CapstoneSubmissions />);

    await waitFor(() => {
      expect(screen.getAllByText('testuser').length).toBeGreaterThan(0);
    });

    expect(screen.getByText('1')).toBeInTheDocument(); // Total count badge
    expect(screen.getAllByText('testuser/capstone-project').length).toBeGreaterThan(0);
  });

  it('displays error state when fetch fails', async () => {
    (apiClient.getCapstoneSubmissions as jest.Mock).mockResolvedValue({
      data: null,
      error: 'Failed to fetch submissions',
    });

    render(<CapstoneSubmissions />);

    await waitFor(() => {
      expect(screen.getByText('Failed to Load Submissions')).toBeInTheDocument();
    });

    expect(screen.getByText('Failed to fetch submissions')).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
  });

  it('displays empty state when no submissions exist', async () => {
    (apiClient.getCapstoneSubmissions as jest.Mock).mockResolvedValue({
      data: {
        submissions: [],
        total_count: 0,
        page: 1,
        page_size: 50,
        total_pages: 0,
      },
      error: null,
    });

    render(<CapstoneSubmissions />);

    await waitFor(() => {
      expect(screen.getByText('No capstone submissions yet')).toBeInTheDocument();
    });

    expect(screen.getByText('0')).toBeInTheDocument(); // Total count badge
  });

  it('renders repository URLs as clickable links with correct attributes', async () => {
    const mockSubmissions = {
      submissions: [
        {
          user_id: 'github|12345678',
          github_username: 'testuser',
          repo_url: 'https://github.com/testuser/capstone-project',
          submitted_at: '2024-01-15T10:30:00Z',
          updated_at: '2024-01-15T10:30:00Z',
        },
      ],
      total_count: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };

    (apiClient.getCapstoneSubmissions as jest.Mock).mockResolvedValue({
      data: mockSubmissions,
      error: null,
    });

    render(<CapstoneSubmissions />);

    await waitFor(() => {
      const link = screen.getAllByRole('link')[0];
      expect(link).toHaveAttribute('href', 'https://github.com/testuser/capstone-project');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });
  });

  it('displays total count badge', async () => {
    const mockSubmissions = {
      submissions: [
        {
          user_id: 'github|12345678',
          github_username: 'testuser',
          repo_url: 'https://github.com/testuser/capstone-project',
          submitted_at: '2024-01-15T10:30:00Z',
          updated_at: '2024-01-15T10:30:00Z',
        },
      ],
      total_count: 42,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };

    (apiClient.getCapstoneSubmissions as jest.Mock).mockResolvedValue({
      data: mockSubmissions,
      error: null,
    });

    render(<CapstoneSubmissions />);

    await waitFor(() => {
      expect(screen.getByText('42')).toBeInTheDocument();
    });
  });

  it('formats timestamps as relative time', async () => {
    const mockSubmissions = {
      submissions: [
        {
          user_id: 'github|12345678',
          github_username: 'testuser',
          repo_url: 'https://github.com/testuser/capstone-project',
          submitted_at: '2024-01-15T10:30:00Z',
          updated_at: '2024-01-15T10:30:00Z',
        },
      ],
      total_count: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };

    (apiClient.getCapstoneSubmissions as jest.Mock).mockResolvedValue({
      data: mockSubmissions,
      error: null,
    });

    render(<CapstoneSubmissions />);

    await waitFor(() => {
      expect(screen.getAllByText('2 hours ago').length).toBeGreaterThan(0);
    });
  });

  it('displays required fields for each submission', async () => {
    const mockSubmissions = {
      submissions: [
        {
          user_id: 'github|12345678',
          github_username: 'testuser',
          repo_url: 'https://github.com/testuser/capstone-project',
          submitted_at: '2024-01-15T10:30:00Z',
          updated_at: '2024-01-15T10:30:00Z',
        },
      ],
      total_count: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };

    (apiClient.getCapstoneSubmissions as jest.Mock).mockResolvedValue({
      data: mockSubmissions,
      error: null,
    });

    render(<CapstoneSubmissions />);

    await waitFor(() => {
      // Verify github_username is displayed
      expect(screen.getAllByText('testuser').length).toBeGreaterThan(0);
      
      // Verify repo_url is displayed
      expect(screen.getAllByText('testuser/capstone-project').length).toBeGreaterThan(0);
      
      // Verify submitted_at is displayed (as relative time)
      expect(screen.getAllByText('2 hours ago').length).toBeGreaterThan(0);
    });
  });
});
