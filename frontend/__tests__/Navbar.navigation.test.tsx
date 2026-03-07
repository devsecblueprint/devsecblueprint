/**
 * Navbar Navigation Tests
 * 
 * Tests for the navigation links in the Navbar component, including:
 * - Visibility based on authentication state
 * - Active state highlighting
 * - Proper navigation to walkthrough pages
 * 
 * Requirements: 16.1, 16.2, 16.3, 16.4, 16.5
 */

import { render, screen } from '@testing-library/react';
import { Navbar } from '@/components/layout/Navbar';
import { ThemeProvider } from '@/components/ThemeProvider';
import { usePathname } from 'next/navigation';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(),
}));

// Helper to render with ThemeProvider
const renderWithTheme = (ui: React.ReactElement) => {
  return render(<ThemeProvider>{ui}</ThemeProvider>);
};

describe('Navbar - Navigation Links', () => {
  const mockUsePathname = usePathname as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    mockUsePathname.mockReturnValue('/');
  });

  describe('Walkthroughs Link Visibility', () => {
    it('should show Walkthroughs link for authenticated users', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const walkthroughsLink = screen.getByRole('link', { name: /walkthroughs/i });
      expect(walkthroughsLink).toBeInTheDocument();
      expect(walkthroughsLink).toHaveAttribute('href', '/walkthroughs');
    });

    it('should not show Walkthroughs link for unauthenticated users', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={false}
        />
      );

      const walkthroughsLink = screen.queryByRole('link', { name: /walkthroughs/i });
      expect(walkthroughsLink).not.toBeInTheDocument();
    });

    it('should show Walkthroughs link with appropriate icon', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const walkthroughsLink = screen.getByRole('link', { name: /walkthroughs/i });
      const svg = walkthroughsLink.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('Active State Highlighting', () => {
    it('should highlight Walkthroughs link when on /walkthroughs page', () => {
      mockUsePathname.mockReturnValue('/walkthroughs');

      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const walkthroughsLink = screen.getByRole('link', { name: /walkthroughs/i });
      expect(walkthroughsLink).toHaveAttribute('aria-current', 'page');
      expect(walkthroughsLink.className).toContain('text-primary-500');
    });

    it('should highlight Walkthroughs link when on /walkthroughs/[id] page', () => {
      mockUsePathname.mockReturnValue('/walkthroughs/test-walkthrough');

      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const walkthroughsLink = screen.getByRole('link', { name: /walkthroughs/i });
      expect(walkthroughsLink).toHaveAttribute('aria-current', 'page');
      expect(walkthroughsLink.className).toContain('text-primary-500');
    });

    it('should highlight Walkthroughs link when on /walkthroughs/[id]/code page', () => {
      mockUsePathname.mockReturnValue('/walkthroughs/test-walkthrough/code');

      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const walkthroughsLink = screen.getByRole('link', { name: /walkthroughs/i });
      expect(walkthroughsLink).toHaveAttribute('aria-current', 'page');
    });

    it('should not highlight Walkthroughs link when on other pages', () => {
      mockUsePathname.mockReturnValue('/dashboard');

      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const walkthroughsLink = screen.getByRole('link', { name: /walkthroughs/i });
      expect(walkthroughsLink).not.toHaveAttribute('aria-current');
    });

    it('should highlight Dashboard link when on /dashboard page', () => {
      mockUsePathname.mockReturnValue('/dashboard');

      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
      expect(dashboardLink).toHaveAttribute('aria-current', 'page');
      expect(dashboardLink.className).toContain('text-primary-500');
    });

    it('should highlight Courses link when on /learn page', () => {
      mockUsePathname.mockReturnValue('/learn');

      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const coursesLink = screen.getByRole('link', { name: /courses/i });
      expect(coursesLink).toHaveAttribute('aria-current', 'page');
      expect(coursesLink.className).toContain('text-primary-500');
    });
  });

  describe('Navigation Links for Authenticated Users', () => {
    it('should show all navigation links for authenticated users', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      expect(screen.getByRole('link', { name: /courses/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /walkthroughs/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument();
    });

    it('should have correct href attributes for all navigation links', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      expect(screen.getByRole('link', { name: /courses/i })).toHaveAttribute('href', '/learn');
      expect(screen.getByRole('link', { name: /walkthroughs/i })).toHaveAttribute('href', '/walkthroughs');
      expect(screen.getByRole('link', { name: /dashboard/i })).toHaveAttribute('href', '/dashboard');
    });
  });

  describe('Mobile Menu Navigation', () => {
    it('should show Walkthroughs link in mobile menu for authenticated users', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      // Open mobile menu
      const mobileMenuButton = screen.getByLabelText('Toggle mobile menu');
      mobileMenuButton.click();

      // Check for Walkthroughs link in mobile menu
      const walkthroughsLinks = screen.getAllByRole('link', { name: /walkthroughs/i });
      expect(walkthroughsLinks.length).toBeGreaterThan(0);
    });

    it('should highlight active link in mobile menu', () => {
      mockUsePathname.mockReturnValue('/walkthroughs');

      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      // Open mobile menu
      const mobileMenuButton = screen.getByLabelText('Toggle mobile menu');
      mobileMenuButton.click();

      // Check for active state in mobile menu
      const walkthroughsLinks = screen.getAllByRole('link', { name: /walkthroughs/i });
      const mobileLink = walkthroughsLinks.find(link => 
        link.className.includes('text-primary-500')
      );
      expect(mobileLink).toBeDefined();
    });
  });
});
