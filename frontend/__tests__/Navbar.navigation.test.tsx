/**
 * Navbar Navigation Tests
 *
 * Tests for the navigation links in the Navbar component, including:
 * - Visibility based on authentication state
 * - Active state highlighting
 * - Proper navigation to walkthrough pages
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
    it('should show Walkthroughs link pointing to /walkthroughs for authenticated users', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const walkthroughsLinks = screen.getAllByRole('link', { name: /walkthroughs/i });
      const authLink = walkthroughsLinks.find(link => link.getAttribute('href') === '/walkthroughs');
      expect(authLink).toBeDefined();
    });

    it('should show Walkthroughs link pointing to /walkthroughs/preview for unauthenticated users', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={false}
        />
      );

      const walkthroughsLinks = screen.getAllByRole('link', { name: /walkthroughs/i });
      const previewLink = walkthroughsLinks.find(link => link.getAttribute('href') === '/walkthroughs/preview');
      expect(previewLink).toBeDefined();
    });

    it('should show Walkthroughs link with appropriate icon', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const walkthroughsLinks = screen.getAllByRole('link', { name: /walkthroughs/i });
      const svg = walkthroughsLinks[0].querySelector('svg');
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

      const walkthroughsLinks = screen.getAllByRole('link', { name: /walkthroughs/i });
      const activeLink = walkthroughsLinks.find(link => link.getAttribute('aria-current') === 'page');
      expect(activeLink).toBeDefined();
      expect(activeLink!.className).toContain('text-primary-500');
    });

    it('should highlight Walkthroughs link when on /walkthroughs/[id] page', () => {
      mockUsePathname.mockReturnValue('/walkthroughs/test-walkthrough');

      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const walkthroughsLinks = screen.getAllByRole('link', { name: /walkthroughs/i });
      const activeLink = walkthroughsLinks.find(link => link.getAttribute('aria-current') === 'page');
      expect(activeLink).toBeDefined();
    });

    it('should highlight Walkthroughs link when on /walkthroughs/[id]/code page', () => {
      mockUsePathname.mockReturnValue('/walkthroughs/test-walkthrough/code');

      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const walkthroughsLinks = screen.getAllByRole('link', { name: /walkthroughs/i });
      const activeLink = walkthroughsLinks.find(link => link.getAttribute('aria-current') === 'page');
      expect(activeLink).toBeDefined();
    });

    it('should not highlight Walkthroughs link when on other pages', () => {
      mockUsePathname.mockReturnValue('/dashboard');

      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const walkthroughsLinks = screen.getAllByRole('link', { name: /walkthroughs/i });
      walkthroughsLinks.forEach(link => {
        expect(link).not.toHaveAttribute('aria-current');
      });
    });

    it('should highlight Dashboard link when on /dashboard page', () => {
      mockUsePathname.mockReturnValue('/dashboard');

      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const dashboardLinks = screen.getAllByRole('link', { name: /dashboard/i });
      const activeLink = dashboardLinks.find(link => link.getAttribute('aria-current') === 'page');
      expect(activeLink).toBeDefined();
      expect(activeLink!.className).toContain('text-primary-500');
    });

    it('should highlight Courses link when on /courses page', () => {
      mockUsePathname.mockReturnValue('/courses');

      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const coursesLinks = screen.getAllByRole('link', { name: /courses/i });
      const activeLink = coursesLinks.find(link => link.className.includes('text-primary-500'));
      expect(activeLink).toBeDefined();
    });
  });

  describe('Navigation Links for Authenticated Users', () => {
    it('should show Courses, Walkthroughs, and Dashboard links for authenticated users', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      expect(screen.getAllByRole('link', { name: /courses/i }).length).toBeGreaterThan(0);
      expect(screen.getAllByRole('link', { name: /walkthroughs/i }).length).toBeGreaterThan(0);
      expect(screen.getAllByRole('link', { name: /dashboard/i }).length).toBeGreaterThan(0);
    });

    it('should have correct href attributes for authenticated navigation links', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const coursesLinks = screen.getAllByRole('link', { name: /courses/i });
      expect(coursesLinks.some(l => l.getAttribute('href') === '/courses')).toBe(true);

      const walkthroughsLinks = screen.getAllByRole('link', { name: /walkthroughs/i });
      expect(walkthroughsLinks.some(l => l.getAttribute('href') === '/walkthroughs')).toBe(true);

      const dashboardLinks = screen.getAllByRole('link', { name: /dashboard/i });
      expect(dashboardLinks.some(l => l.getAttribute('href') === '/dashboard')).toBe(true);
    });
  });

  describe('Videos Link', () => {
    it('should show Videos link pointing to /videos for authenticated users', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const videosLinks = screen.getAllByRole('link', { name: /videos/i });
      expect(videosLinks.some(l => l.getAttribute('href') === '/videos')).toBe(true);
    });

    it('should show Videos link pointing to /videos/preview for unauthenticated users', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={false}
        />
      );

      const videosLinks = screen.getAllByRole('link', { name: /videos/i });
      expect(videosLinks.some(l => l.getAttribute('href') === '/videos/preview')).toBe(true);
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
