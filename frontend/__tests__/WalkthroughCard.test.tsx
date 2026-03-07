/**
 * WalkthroughCard Component Tests
 * 
 * Tests for the WalkthroughCard component including:
 * - Display of title, description, difficulty badge
 * - Display of topics and estimated time
 * - Display of progress indicator
 * - Clickable navigation to detail page
 */

import { render, screen } from '@testing-library/react';
import { WalkthroughCard } from '@/components/WalkthroughCard';
import { WalkthroughWithProgress } from '@/lib/types';

describe('WalkthroughCard', () => {
  const mockWalkthrough: WalkthroughWithProgress = {
    id: 'secure-cicd-pipeline',
    title: 'Building a Secure CI/CD Pipeline',
    description: 'Learn how to implement security controls in a CI/CD pipeline using GitHub Actions, container scanning, and automated security testing.',
    difficulty: 'Intermediate',
    topics: ['CI/CD', 'Container Security', 'GitHub Actions', 'SAST', 'DAST'],
    estimatedTime: 90,
    prerequisites: ['secure-sdlc', 'container-basics'],
    repository: 'walkthroughs/secure-cicd-pipeline',
    progress: {
      status: 'not_started',
    },
  };

  it('should display walkthrough title', () => {
    render(<WalkthroughCard walkthrough={mockWalkthrough} />);
    expect(screen.getByText('Building a Secure CI/CD Pipeline')).toBeInTheDocument();
  });

  it('should display walkthrough description', () => {
    render(<WalkthroughCard walkthrough={mockWalkthrough} />);
    expect(screen.getByText(/Learn how to implement security controls/)).toBeInTheDocument();
  });

  it('should display difficulty badge', () => {
    render(<WalkthroughCard walkthrough={mockWalkthrough} />);
    expect(screen.getByText('Intermediate')).toBeInTheDocument();
  });

  it('should display topic tags', () => {
    render(<WalkthroughCard walkthrough={mockWalkthrough} />);
    expect(screen.getByText('CI/CD')).toBeInTheDocument();
    expect(screen.getByText('Container Security')).toBeInTheDocument();
    expect(screen.getByText('GitHub Actions')).toBeInTheDocument();
  });

  it('should display estimated time', () => {
    render(<WalkthroughCard walkthrough={mockWalkthrough} />);
    expect(screen.getByText('90 min')).toBeInTheDocument();
  });

  it('should display progress indicator for not_started status', () => {
    render(<WalkthroughCard walkthrough={mockWalkthrough} />);
    expect(screen.getByText('Not Started')).toBeInTheDocument();
  });

  it('should display progress indicator for in_progress status', () => {
    const inProgressWalkthrough = {
      ...mockWalkthrough,
      progress: {
        status: 'in_progress' as const,
        startedAt: '2024-01-15T10:30:00Z',
      },
    };
    render(<WalkthroughCard walkthrough={inProgressWalkthrough} />);
    expect(screen.getByText('In Progress')).toBeInTheDocument();
  });

  it('should display progress indicator for completed status', () => {
    const completedWalkthrough = {
      ...mockWalkthrough,
      progress: {
        status: 'completed' as const,
        startedAt: '2024-01-15T10:30:00Z',
        completedAt: '2024-01-15T12:00:00Z',
      },
    };
    render(<WalkthroughCard walkthrough={completedWalkthrough} />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('should render as a clickable link to detail page', () => {
    render(<WalkthroughCard walkthrough={mockWalkthrough} />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/walkthroughs/secure-cicd-pipeline');
  });

  it('should display correct difficulty badge variant for Beginner', () => {
    const beginnerWalkthrough = {
      ...mockWalkthrough,
      difficulty: 'Beginner' as const,
    };
    render(<WalkthroughCard walkthrough={beginnerWalkthrough} />);
    expect(screen.getByText('Beginner')).toBeInTheDocument();
  });

  it('should display correct difficulty badge variant for Advanced', () => {
    const advancedWalkthrough = {
      ...mockWalkthrough,
      difficulty: 'Advanced' as const,
    };
    render(<WalkthroughCard walkthrough={advancedWalkthrough} />);
    expect(screen.getByText('Advanced')).toBeInTheDocument();
  });

  it('should limit displayed topics to 3 and show count for additional topics', () => {
    render(<WalkthroughCard walkthrough={mockWalkthrough} />);
    // First 3 topics should be visible
    expect(screen.getByText('CI/CD')).toBeInTheDocument();
    expect(screen.getByText('Container Security')).toBeInTheDocument();
    expect(screen.getByText('GitHub Actions')).toBeInTheDocument();
    // Should show "+2 more" for remaining topics
    expect(screen.getByText('+2 more')).toBeInTheDocument();
  });

  it('should not show additional topics indicator when 3 or fewer topics', () => {
    const fewTopicsWalkthrough = {
      ...mockWalkthrough,
      topics: ['CI/CD', 'Security'],
    };
    render(<WalkthroughCard walkthrough={fewTopicsWalkthrough} />);
    expect(screen.queryByText(/\+\d+ more/)).not.toBeInTheDocument();
  });
});
