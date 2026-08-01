import React from 'react';
import { render, screen } from '@testing-library/react';
import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import type { ContributorRole } from '@/lib/types';

// Mock next/link to render as a plain anchor for testing
jest.mock('next/link', () => {
  return ({ href, children, ...props }: any) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

describe('DashboardHeader', () => {
  const defaultProps = {
    username: 'testuser',
    isAdmin: false,
    contributorRole: null,
    isLoading: false,
  };

  it('renders personalized welcome message with username', () => {
    render(<DashboardHeader {...defaultProps} />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Welcome back, testuser'
    );
  });

  it('renders generic welcome when username is null', () => {
    render(<DashboardHeader {...defaultProps} username={null} />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Welcome back'
    );
    expect(
      screen.getByRole('heading', { level: 1 }).textContent
    ).not.toContain(',');
  });

  it('renders generic welcome when username is empty string', () => {
    render(<DashboardHeader {...defaultProps} username="" />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Welcome back'
    );
  });

  it('renders generic welcome when username is whitespace only', () => {
    render(<DashboardHeader {...defaultProps} username="   " />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Welcome back'
    );
  });

  it('truncates username to max 50 characters', () => {
    const longUsername = 'a'.repeat(60);
    render(<DashboardHeader {...defaultProps} username={longUsername} />);
    const heading = screen.getByRole('heading', { level: 1 });
    // "Welcome back, " is 14 chars + 50 chars of username = 64 total max
    expect(heading.textContent).toBe(`Welcome back, ${'a'.repeat(50)}`);
  });

  it('shows full username when 50 characters or fewer', () => {
    const username = 'a'.repeat(50);
    render(<DashboardHeader {...defaultProps} username={username} />);
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading.textContent).toBe(`Welcome back, ${username}`);
  });

  it('renders static subtitle', () => {
    render(<DashboardHeader {...defaultProps} />);
    expect(
      screen.getByText(
        'Continue building your DevSecOps and Cloud Security skills.'
      )
    ).toBeInTheDocument();
  });

  it('renders View All Courses link pointing to /courses', () => {
    render(<DashboardHeader {...defaultProps} />);
    const link = screen.getByRole('link', { name: /view all courses/i });
    expect(link).toHaveAttribute('href', '/courses');
  });

  it('shows contributor badge when contributorRole is present', () => {
    const contributorRole: ContributorRole = {
      role: 'contributor',
      assigned_by: 'admin',
      assigned_at: '2024-01-01',
      note: 'Great work!',
    };
    render(
      <DashboardHeader {...defaultProps} contributorRole={contributorRole} />
    );
    expect(screen.getByText('Contributor')).toBeInTheDocument();
  });

  it('does not show contributor badge when contributorRole is null', () => {
    render(<DashboardHeader {...defaultProps} contributorRole={null} />);
    expect(screen.queryByText('Contributor')).not.toBeInTheDocument();
  });

  it('shows admin link to /admin when isAdmin is true', () => {
    render(<DashboardHeader {...defaultProps} isAdmin={true} />);
    const adminLink = screen.getByRole('link', { name: /admin/i });
    expect(adminLink).toHaveAttribute('href', '/admin');
  });

  it('does not show admin link when isAdmin is false', () => {
    render(<DashboardHeader {...defaultProps} isAdmin={false} />);
    expect(screen.queryByRole('link', { name: /admin/i })).not.toBeInTheDocument();
  });

  it('displays both contributor badge and admin link when both are present', () => {
    const contributorRole: ContributorRole = {
      role: 'contributor',
      assigned_by: 'admin',
      assigned_at: '2024-01-01',
      note: 'Contributed a lot!',
    };
    render(
      <DashboardHeader
        {...defaultProps}
        isAdmin={true}
        contributorRole={contributorRole}
      />
    );
    expect(screen.getByText('Contributor')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /admin/i })).toBeInTheDocument();
  });

  it('displays skeleton placeholder when isLoading is true', () => {
    const { container } = render(
      <DashboardHeader {...defaultProps} isLoading={true} />
    );
    // Should not render the heading or subtitle
    expect(screen.queryByRole('heading', { level: 1 })).not.toBeInTheDocument();
    // Should show animated pulse elements
    const pulseElements = container.querySelectorAll('.animate-pulse');
    expect(pulseElements.length).toBeGreaterThan(0);
  });

  it('does not display content when loading', () => {
    render(<DashboardHeader {...defaultProps} isLoading={true} />);
    expect(screen.queryByText(/welcome back/i)).not.toBeInTheDocument();
    expect(
      screen.queryByText(
        'Continue building your DevSecOps and Cloud Security skills.'
      )
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: /view all courses/i })
    ).not.toBeInTheDocument();
  });

  it('uses h1 element for the welcome message', () => {
    render(<DashboardHeader {...defaultProps} />);
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading.tagName).toBe('H1');
  });
});
