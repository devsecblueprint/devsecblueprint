import React from 'react';
import { render, screen } from '@testing-library/react';
import { AchievementsPanel } from '@/components/dashboard/AchievementsPanel';
import type { Badge } from '@/lib/types';

describe('AchievementsPanel', () => {
  const mockBadges: Badge[] = [
    { id: '1', title: 'First Steps', description: 'Complete your first lesson', icon: '🎯', earned: true, earnedDate: '2024-01-01' },
    { id: '2', title: 'Quiz Master', description: 'Pass 5 quizzes', icon: '📝', earned: true, earnedDate: '2024-02-01' },
    { id: '3', title: 'Explorer', description: 'Start 3 walkthroughs', icon: '🔍', earned: false },
    { id: '4', title: 'Streak Star', description: '7 day streak', icon: '⭐', earned: false },
  ];

  const defaultProps = {
    badges: mockBadges,
    isLoading: false,
    error: null,
  };

  it('renders h2 heading "Achievements"', () => {
    render(<AchievementsPanel {...defaultProps} />);
    const heading = screen.getByRole('heading', { level: 2, name: 'Achievements' });
    expect(heading).toBeInTheDocument();
  });

  it('renders earned badges at full opacity', () => {
    const { container } = render(<AchievementsPanel {...defaultProps} />);
    // Earned badges should have opacity-100 class
    const badgeCards = container.querySelectorAll('.opacity-100');
    expect(badgeCards.length).toBe(2);
  });

  it('renders locked badges at 0.4 opacity', () => {
    const { container } = render(<AchievementsPanel {...defaultProps} />);
    // Locked badges should have opacity-40 class
    const badgeCards = container.querySelectorAll('.opacity-40');
    expect(badgeCards.length).toBe(2);
  });

  it('displays "Earned" text label for earned badges', () => {
    render(<AchievementsPanel {...defaultProps} />);
    const earnedLabels = screen.getAllByText('Earned');
    expect(earnedLabels.length).toBe(2);
  });

  it('displays "Locked" text label for locked badges', () => {
    render(<AchievementsPanel {...defaultProps} />);
    const lockedLabels = screen.getAllByText('Locked');
    expect(lockedLabels.length).toBe(2);
  });

  it('displays badge icons and titles', () => {
    render(<AchievementsPanel {...defaultProps} />);
    expect(screen.getByText('First Steps')).toBeInTheDocument();
    expect(screen.getByText('Quiz Master')).toBeInTheDocument();
    expect(screen.getByText('Explorer')).toBeInTheDocument();
    expect(screen.getByText('Streak Star')).toBeInTheDocument();
  });

  it('shows "View All" with earned count when total badges > 6', () => {
    const manyBadges: Badge[] = Array.from({ length: 8 }, (_, i) => ({
      id: String(i),
      title: `Badge ${i}`,
      description: `Description ${i}`,
      icon: '🏆',
      earned: i < 3,
    }));
    render(<AchievementsPanel badges={manyBadges} isLoading={false} error={null} />);
    expect(screen.getByText('View All (3 earned)')).toBeInTheDocument();
  });

  it('does not show "View All" when total badges <= 6', () => {
    render(<AchievementsPanel {...defaultProps} />);
    expect(screen.queryByText(/View All/)).not.toBeInTheDocument();
  });

  it('only displays first 6 badges when total > 6', () => {
    const manyBadges: Badge[] = Array.from({ length: 8 }, (_, i) => ({
      id: String(i),
      title: `Badge ${i}`,
      description: `Description ${i}`,
      icon: '🏆',
      earned: i < 3,
    }));
    render(<AchievementsPanel badges={manyBadges} isLoading={false} error={null} />);
    // Should show only 6 badge titles
    expect(screen.getByText('Badge 0')).toBeInTheDocument();
    expect(screen.getByText('Badge 5')).toBeInTheDocument();
    expect(screen.queryByText('Badge 6')).not.toBeInTheDocument();
    expect(screen.queryByText('Badge 7')).not.toBeInTheDocument();
  });

  it('shows 6 skeleton badge cards while loading', () => {
    const { container } = render(
      <AchievementsPanel badges={[]} isLoading={true} error={null} />
    );
    // SkeletonBadgeCard renders divs with animate-pulse inside
    const skeletonCards = container.querySelectorAll('.animate-pulse');
    expect(skeletonCards.length).toBeGreaterThanOrEqual(6);
  });

  it('shows empty state on error (no raw error message)', () => {
    render(
      <AchievementsPanel badges={[]} isLoading={false} error="Network error: failed to fetch" />
    );
    // Should not display the raw error message
    expect(screen.queryByText(/Network error/)).not.toBeInTheDocument();
    // Should display a friendly empty state
    expect(screen.getByText('No badges to display right now.')).toBeInTheDocument();
  });

  it('shows empty state when no badges and no error', () => {
    render(<AchievementsPanel badges={[]} isLoading={false} error={null} />);
    expect(screen.getByText('Start learning to earn your first badge!')).toBeInTheDocument();
  });

  it('uses aria-labelledby for section accessibility', () => {
    const { container } = render(<AchievementsPanel {...defaultProps} />);
    const section = container.querySelector('section');
    expect(section).toHaveAttribute('aria-labelledby', 'achievements-heading');
  });

  it('marks badge icons as aria-hidden', () => {
    const { container } = render(<AchievementsPanel {...defaultProps} />);
    const hiddenIcons = container.querySelectorAll('[aria-hidden="true"]');
    expect(hiddenIcons.length).toBeGreaterThan(0);
  });
});
