import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { UserList } from '@/components/admin/UserList';
import { apiClient } from '@/lib/api';

// Mock the API client
jest.mock('@/lib/api', () => ({
  apiClient: {
    listUsers: jest.fn(),
    getAdminUserProfile: jest.fn(),
  },
}));

// Mock date-fns
jest.mock('date-fns', () => ({
  format: jest.fn((date: Date) => 'Jan 15, 2024'),
}));

// Mock UserProfileModal to avoid nested fetch complexity
jest.mock('@/components/admin/UserProfileModal', () => ({
  UserProfileModal: ({ userId, onClose }: { userId: string; onClose: () => void }) => (
    <div data-testid="user-profile-modal" data-user-id={userId}>
      <button onClick={onClose}>Close Modal</button>
    </div>
  ),
}));

const mockUsers = [
  {
    user_id: 'github|111',
    username: 'Alice',
    github_username: 'alice-gh',
    gitlab_username: '',
    provider: 'github',
    avatar_url: 'https://example.com/alice.png',
    registered_at: '2024-01-15T10:30:00Z',
    last_login: '2024-03-25T08:00:00Z',
  },
  {
    user_id: 'gitlab|222',
    username: 'Bob',
    github_username: '',
    gitlab_username: 'bob-gl',
    provider: 'gitlab',
    avatar_url: '',
    registered_at: '2024-02-10T12:00:00Z',
    last_login: '2024-03-20T09:00:00Z',
  },
];

const mockResponse = {
  data: {
    users: mockUsers,
    total_count: 42,
    page: 1,
    page_size: 20,
    total_pages: 3,
  },
  error: null,
};

describe('UserList', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('displays loading state initially', () => {
    (apiClient.listUsers as jest.Mock).mockImplementation(() => new Promise(() => {}));
    render(<UserList />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders user table after successful fetch', async () => {
    (apiClient.listUsers as jest.Mock).mockResolvedValue(mockResponse);
    render(<UserList />);

    await waitFor(() => {
      expect(screen.getAllByText('Alice').length).toBeGreaterThan(0);
    });

    expect(screen.getAllByText('Bob').length).toBeGreaterThan(0);
    expect(screen.getAllByText('@alice-gh').length).toBeGreaterThan(0);
    expect(screen.getAllByText('@bob-gl').length).toBeGreaterThan(0);
    expect(screen.getAllByText('GitHub').length).toBeGreaterThan(0);
    expect(screen.getAllByText('GitLab').length).toBeGreaterThan(0);
  });

  it('displays total count badge', async () => {
    (apiClient.listUsers as jest.Mock).mockResolvedValue(mockResponse);
    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText('42')).toBeInTheDocument();
    });
  });

  it('displays error state when fetch fails', async () => {
    (apiClient.listUsers as jest.Mock).mockResolvedValue({
      data: null,
      error: 'Failed to retrieve users',
    });
    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText('Failed to retrieve users')).toBeInTheDocument();
    });

    expect(screen.getByText('Try Again')).toBeInTheDocument();
  });

  it('displays empty state when no users', async () => {
    (apiClient.listUsers as jest.Mock).mockResolvedValue({
      data: { users: [], total_count: 0, page: 1, page_size: 20, total_pages: 0 },
      error: null,
    });
    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText('No users found')).toBeInTheDocument();
    });
  });

  it('filters users client-side by search input', async () => {
    (apiClient.listUsers as jest.Mock).mockResolvedValue(mockResponse);
    render(<UserList />);

    await waitFor(() => {
      expect(screen.getAllByText('Alice').length).toBeGreaterThan(0);
    });

    const searchInput = screen.getByPlaceholderText('Filter by username...');
    fireEvent.change(searchInput, { target: { value: 'bob' } });

    expect(screen.queryAllByText('Alice')).toHaveLength(0);
    expect(screen.getAllByText('Bob').length).toBeGreaterThan(0);
  });

  it('shows no-match message when filter has no results', async () => {
    (apiClient.listUsers as jest.Mock).mockResolvedValue(mockResponse);
    render(<UserList />);

    await waitFor(() => {
      expect(screen.getAllByText('Alice').length).toBeGreaterThan(0);
    });

    const searchInput = screen.getByPlaceholderText('Filter by username...');
    fireEvent.change(searchInput, { target: { value: 'zzz' } });

    expect(screen.getByText(/No users matching/)).toBeInTheDocument();
  });

  it('shows pagination controls with page info', async () => {
    (apiClient.listUsers as jest.Mock).mockResolvedValue(mockResponse);
    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 3 · 42 users')).toBeInTheDocument();
    });

    expect(screen.getByText('Previous')).toBeDisabled();
    expect(screen.getByText('Next')).not.toBeDisabled();
  });

  it('navigates to next page on Next click', async () => {
    (apiClient.listUsers as jest.Mock).mockResolvedValue(mockResponse);
    render(<UserList />);

    await waitFor(() => {
      expect(screen.getAllByText('Alice').length).toBeGreaterThan(0);
    });

    // Mock page 2 response
    (apiClient.listUsers as jest.Mock).mockResolvedValue({
      data: {
        users: [{ ...mockUsers[0], user_id: 'github|333', username: 'Charlie' }],
        total_count: 42,
        page: 2,
        page_size: 20,
        total_pages: 3,
      },
      error: null,
    });

    fireEvent.click(screen.getByText('Next'));

    await waitFor(() => {
      expect(apiClient.listUsers).toHaveBeenCalledWith(2, 20);
    });
  });

  it('opens UserProfileModal when a row is clicked', async () => {
    (apiClient.listUsers as jest.Mock).mockResolvedValue(mockResponse);
    render(<UserList />);

    await waitFor(() => {
      expect(screen.getAllByText('Alice').length).toBeGreaterThan(0);
    });

    // Click the first Alice element (desktop table row)
    fireEvent.click(screen.getAllByText('Alice')[0]);

    await waitFor(() => {
      const modal = screen.getByTestId('user-profile-modal');
      expect(modal).toBeInTheDocument();
      expect(modal).toHaveAttribute('data-user-id', 'github|111');
    });
  });

  it('closes UserProfileModal when close is triggered', async () => {
    (apiClient.listUsers as jest.Mock).mockResolvedValue(mockResponse);
    render(<UserList />);

    await waitFor(() => {
      expect(screen.getAllByText('Alice').length).toBeGreaterThan(0);
    });

    fireEvent.click(screen.getAllByText('Alice')[0]);

    await waitFor(() => {
      expect(screen.getByTestId('user-profile-modal')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Close Modal'));

    await waitFor(() => {
      expect(screen.queryByTestId('user-profile-modal')).not.toBeInTheDocument();
    });
  });

  it('retries fetch when Try Again is clicked', async () => {
    (apiClient.listUsers as jest.Mock).mockResolvedValueOnce({
      data: null,
      error: 'Network error',
    });
    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    (apiClient.listUsers as jest.Mock).mockResolvedValueOnce(mockResponse);
    fireEvent.click(screen.getByText('Try Again'));

    await waitFor(() => {
      expect(screen.getAllByText('Alice').length).toBeGreaterThan(0);
    });
  });
});
