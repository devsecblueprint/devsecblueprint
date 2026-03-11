/**
 * Curriculum Integration Tests
 * 
 * Tests for the curriculum link integration in the Navbar component:
 * - Curriculum link should appear for unauthenticated users only
 * - Curriculum link should not appear for authenticated users
 * 
 * Requirements: 1.1
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

describe('Navbar - Curriculum Link Integration', () => {
  const mockUsePathname = usePathname as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    mockUsePathname.mockReturnValue('/');
  });

  describe('Curriculum Link Visibility', () => {
    it('should show Curriculum link for unauthenticated users', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={false}
        />
      );

      const curriculumLink = screen.getByRole('link', { name: /curriculum/i });
      expect(curriculumLink).toBeInTheDocument();
      expect(curriculumLink).toHaveAttribute('href', '/curriculum');
    });

    it('should not show Curriculum link for authenticated users', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      const curriculumLink = screen.queryByRole('link', { name: /curriculum/i });
      expect(curriculumLink).not.toBeInTheDocument();
    });

    it('should show Curriculum link with appropriate icon for unauthenticated users', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={false}
        />
      );

      const curriculumLink = screen.getByRole('link', { name: /curriculum/i });
      const svg = curriculumLink.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('Active State Highlighting', () => {
    it('should highlight Curriculum link when on /curriculum page', () => {
      mockUsePathname.mockReturnValue('/curriculum');

      renderWithTheme(
        <Navbar
          isAuthenticated={false}
        />
      );

      const curriculumLink = screen.getByRole('link', { name: /curriculum/i });
      expect(curriculumLink).toHaveAttribute('aria-current', 'page');
      expect(curriculumLink.className).toContain('text-primary-500');
    });

    it('should not highlight Curriculum link when on other pages', () => {
      mockUsePathname.mockReturnValue('/');

      renderWithTheme(
        <Navbar
          isAuthenticated={false}
        />
      );

      const curriculumLink = screen.getByRole('link', { name: /curriculum/i });
      expect(curriculumLink).not.toHaveAttribute('aria-current');
    });
  });

  describe('Mobile Menu Navigation', () => {
    it('should show Curriculum link in mobile menu for unauthenticated users', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={false}
        />
      );

      // Open mobile menu
      const mobileMenuButton = screen.getByLabelText('Toggle mobile menu');
      mobileMenuButton.click();

      // Check for Curriculum link in mobile menu
      const curriculumLinks = screen.getAllByRole('link', { name: /curriculum/i });
      expect(curriculumLinks.length).toBeGreaterThan(0);
    });

    it('should not show Curriculum link in mobile menu for authenticated users', () => {
      renderWithTheme(
        <Navbar
          isAuthenticated={true}
          userName="Test User"
        />
      );

      // Open mobile menu
      const mobileMenuButton = screen.getByLabelText('Toggle mobile menu');
      mobileMenuButton.click();

      // Check that Curriculum link is not in mobile menu
      const curriculumLinks = screen.queryAllByRole('link', { name: /curriculum/i });
      expect(curriculumLinks.length).toBe(0);
    });

    it('should highlight active Curriculum link in mobile menu', () => {
      mockUsePathname.mockReturnValue('/curriculum');

      renderWithTheme(
        <Navbar
          isAuthenticated={false}
        />
      );

      // Open mobile menu
      const mobileMenuButton = screen.getByLabelText('Toggle mobile menu');
      mobileMenuButton.click();

      // Check for active state in mobile menu
      const curriculumLinks = screen.getAllByRole('link', { name: /curriculum/i });
      const mobileLink = curriculumLinks.find(link => 
        link.className.includes('text-primary-500')
      );
      expect(mobileLink).toBeDefined();
    });
  });
});
