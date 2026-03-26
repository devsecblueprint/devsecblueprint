import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { UserProfileModal } from '@/components/admin/UserProfileModal';
import { apiClient } from '@/lib/api';

// Mock the API client
jest.mock('@/lib/api', () => ({
  apiClient: {
    getAdminUserProfile: jest.fn(),
  },
}));

// Mock date-fns
jest.mock('date-fns', () => ({
  format: jest.fn(() => 'Jan 15, 2024'),
}));

const mockProfile = {
  user: {
    user_id: 'github|12345678',
    username: 'Test User',
    github_username: 'testuser',
    gitlab_username: '',
    provider: 'github',
    avatar_url: 'https://example.com/avatar.png',
    registered_at: '2024-01-15T10:30:00Z',
    last_login: '2024-03-25T08:00:00Z',
  },
  stats: {
    completed_count: 42,
    overall_completion: 43.8,
    quizzes_passed: 10,
    walkthroughs_completed: 3,
    capstone_submissions: 1,
    current_streak: 5,
    longest_streak: 12,
  },
  badges: [
    { id: 'b1', title: 'First Steps', icon: '🎯', earned: true, earned_date: '2024-01-16T00:00:00Z' },
    { id: 'b2', title: 'Quiz Master', icon: '🧠', earned: false },
  ],
};

describe('UserProfileModal', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('displays loading state initially', () => {
    (apiClient.getAdminUserProfile as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    );

    render(<UserProfileModal userId="github|12345678" onClose={mockOnClose} />);

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('displays user profile after successful fetch', async () => {
    (apiClient.getAdminUserProfile as jest.Mock).mockResolvedValue({
      data: mockProfile,
      error: null,
    });

    render(<UserProfileModal userId="github|12345678" onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });

    expect(screen.getByText('@testuser')).toBeInTheDocument();
    expect(screen.getByText('GitHub')).toBeInTheDocument();
  });

  it('displays stats grid with correct values', async () => {
    (apiClient.getAdminUserProfile as jest.Mock).mockResolvedValue({
      data: mockProfile,
      error: null,
    });

    render(<UserProfileModal userId="github|12345678" onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText('42')).toBeInTheDocument(); // Lessons
    });

    expect(screen.getByText('3')).toBeInTheDocument(); // Walkthroughs
    expect(screen.getByText('10')).toBeInTheDocument(); // Quizzes
    expect(screen.getByText('43.8%')).toBeInTheDocument(); // Completion
    // Badges earned (1) and Capstones (1) both show "1"
    expect(screen.getAllByText('1')).toHaveLength(2);
    // "Badges" appears as both stat label and section heading
    expect(screen.getAllByText('Badges')).toHaveLength(2);
    expect(screen.getByText('Capstones')).toBeInTheDocument();
  });

  it('displays badges with earned/unearned state', async () => {
    (apiClient.getAdminUserProfile as jest.Mock).mockResolvedValue({
      data: mockProfile,
      error: null,
    });

    render(<UserProfileModal userId="github|12345678" onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText('First Steps')).toBeInTheDocument();
    });

    expect(screen.getByText('Quiz Master')).toBeInTheDocument();
    expect(screen.getByText('🎯')).toBeInTheDocument();
    expect(screen.getByText('🧠')).toBeInTheDocument();
  });

  it('displays error state when fetch fails', async () => {
    (apiClient.getAdminUserProfile as jest.Mock).mockResolvedValue({
      data: null,
      error: 'User not found',
    });

    render(<UserProfileModal userId="unknown" onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText('User not found')).toBeInTheDocument();
    });

    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('has correct accessibility attributes', () => {
    (apiClient.getAdminUserProfile as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    );

    render(<UserProfileModal userId="github|12345678" onClose={mockOnClose} />);

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', 'user-profile-title');
  });

  it('calls onClose when Escape key is pressed', async () => {
    (apiClient.getAdminUserProfile as jest.Mock).mockResolvedValue({
      data: mockProfile,
      error: null,
    });

    render(<UserProfileModal userId="github|12345678" onClose={mockOnClose} />);

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when close button is clicked', async () => {
    (apiClient.getAdminUserProfile as jest.Mock).mockResolvedValue({
      data: mockProfile,
      error: null,
    });

    render(<UserProfileModal userId="github|12345678" onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });

    const closeButton = screen.getByLabelText('Close modal');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('displays GitLab provider badge for GitLab users', async () => {
    const gitlabProfile = {
      ...mockProfile,
      user: {
        ...mockProfile.user,
        provider: 'gitlab',
        gitlab_username: 'gitlabuser',
        github_username: '',
      },
    };

    (apiClient.getAdminUserProfile as jest.Mock).mockResolvedValue({
      data: gitlabProfile,
      error: null,
    });

    render(<UserProfileModal userId="gitlab|12345678" onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText('GitLab')).toBeInTheDocument();
    });

    expect(screen.getByText('@gitlabuser')).toBeInTheDocument();
  });
});
