import React from 'react';
import { render, screen } from '@testing-library/react';
import { LearningSummaryGrid } from '@/components/dashboard/LearningSummaryGrid';

// Mock useUserStats hook
const mockUseUserStats = jest.fn();
jest.mock('@/lib/hooks/useUserStats', () => ({
  useUserStats: () => mockUseUserStats(),
}));

describe('LearningSummaryGrid', () => {
  const defaultStats = {
    currentStreak: 5,
    longestStreak: 12,
    overallCompletion: 67,
    quizzesPassed: 8,
    walkthroughsCompleted: 3,
    completedCount: 11,
    isLoading: false,
    error: null,
    refetch: jest.fn(),
    clearError: jest.fn(),
  };

  beforeEach(() => {
    mockUseUserStats.mockReturnValue(defaultStats);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders section heading "Learning Summary"', () => {
    render(<LearningSummaryGrid />);
    expect(
      screen.getByRole('heading', { level: 2, name: /learning summary/i })
    ).toBeInTheDocument();
  });

  it('renders 4 metric cards with correct values', () => {
    render(<LearningSummaryGrid />);
    // Overall Completion uses ProgressRing - check for progressbar role
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '67');
    // Quizzes Passed
    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText('Quizzes Passed')).toBeInTheDocument();
    // Walkthroughs Completed
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('Walkthroughs Completed')).toBeInTheDocument();
    // Current Streak
    expect(screen.getByText('5 days')).toBeInTheDocument();
    expect(screen.getByText('Current Streak')).toBeInTheDocument();
    // Longest streak muted text
    expect(screen.getByText('Longest: 12 days')).toBeInTheDocument();
  });

  it('shows "Overall Completion" card with title and description', () => {
    render(<LearningSummaryGrid />);
    expect(screen.getByText('Overall Completion')).toBeInTheDocument();
    expect(screen.getByText('Total progress across all courses')).toBeInTheDocument();
  });

  it('shows skeleton cards while loading', () => {
    mockUseUserStats.mockReturnValue({ ...defaultStats, isLoading: true });
    const { container } = render(<LearningSummaryGrid />);
    // Should not show metric values
    expect(screen.queryByText('Quizzes Passed')).not.toBeInTheDocument();
    // Should show animated pulse skeleton elements
    const pulseElements = container.querySelectorAll('.animate-pulse');
    expect(pulseElements.length).toBeGreaterThan(0);
  });

  it('displays zero values on error without error message', () => {
    mockUseUserStats.mockReturnValue({
      ...defaultStats,
      currentStreak: 0,
      longestStreak: 0,
      overallCompletion: 0,
      quizzesPassed: 0,
      walkthroughsCompleted: 0,
      isLoading: false,
      error: 'Failed to fetch statistics',
    });
    render(<LearningSummaryGrid />);
    // Should render the cards with zero values
    expect(screen.getByText('Quizzes Passed')).toBeInTheDocument();
    expect(screen.getByText('0 days')).toBeInTheDocument();
    // Should NOT display any error message to the user
    expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/failed/i)).not.toBeInTheDocument();
  });

  it('uses singular "day" when streak is 1', () => {
    mockUseUserStats.mockReturnValue({
      ...defaultStats,
      currentStreak: 1,
      longestStreak: 1,
    });
    render(<LearningSummaryGrid />);
    expect(screen.getByText('1 day')).toBeInTheDocument();
    expect(screen.getByText('Longest: 1 day')).toBeInTheDocument();
  });

  it('uses the responsive grid classes', () => {
    const { container } = render(<LearningSummaryGrid />);
    const grid = container.querySelector('.grid');
    expect(grid).toHaveClass('grid-cols-1');
    expect(grid).toHaveClass('md:grid-cols-2');
    expect(grid).toHaveClass('lg:grid-cols-4');
  });

  it('uses semantic section element with aria-labelledby', () => {
    const { container } = render(<LearningSummaryGrid />);
    const section = container.querySelector('section');
    expect(section).toHaveAttribute('aria-labelledby', 'learning-summary-heading');
    const heading = screen.getByRole('heading', { level: 2 });
    expect(heading).toHaveAttribute('id', 'learning-summary-heading');
  });
});
