/**
 * WalkthroughLink Component Tests
 *
 * Tests for the WalkthroughLink component which fetches walkthrough data
 * from /api/walkthroughs/:id and displays a styled card.
 */

import { render, screen, waitFor } from '@testing-library/react';
import { WalkthroughLink } from '@/components/WalkthroughLink';

// Mock global fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('WalkthroughLink', () => {
  const mockWalkthrough = {
    id: 'test-walkthrough',
    title: 'Test Walkthrough',
    description: 'This is a test walkthrough for unit testing',
    difficulty: 'Intermediate' as const,
    topics: ['Testing', 'React', 'TypeScript'],
    estimatedTime: 45,
    prerequisites: [],
    repository: 'walkthroughs/test-walkthrough',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Valid Walkthrough ID', () => {
    beforeEach(() => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockWalkthrough),
      });
    });

    it('should render walkthrough card with title', async () => {
      render(<WalkthroughLink walkthroughId="test-walkthrough" />);

      await waitFor(() => {
        expect(screen.getByText('Test Walkthrough')).toBeInTheDocument();
      });
    });

    it('should render walkthrough description', async () => {
      render(<WalkthroughLink walkthroughId="test-walkthrough" />);

      await waitFor(() => {
        expect(screen.getByText('This is a test walkthrough for unit testing')).toBeInTheDocument();
      });
    });

    it('should render difficulty badge', async () => {
      render(<WalkthroughLink walkthroughId="test-walkthrough" />);

      await waitFor(() => {
        expect(screen.getByText('Intermediate')).toBeInTheDocument();
      });
    });

    it('should render estimated time', async () => {
      render(<WalkthroughLink walkthroughId="test-walkthrough" />);

      await waitFor(() => {
        expect(screen.getByText('45 minutes')).toBeInTheDocument();
      });
    });

    it('should render topics', async () => {
      render(<WalkthroughLink walkthroughId="test-walkthrough" />);

      await waitFor(() => {
        expect(screen.getByText('Testing')).toBeInTheDocument();
        expect(screen.getByText('React')).toBeInTheDocument();
        expect(screen.getByText('TypeScript')).toBeInTheDocument();
      });
    });

    it('should render "View Walkthrough" call to action', async () => {
      render(<WalkthroughLink walkthroughId="test-walkthrough" />);

      await waitFor(() => {
        expect(screen.getByText('View Walkthrough')).toBeInTheDocument();
      });
    });

    it('should have link to walkthrough detail page', async () => {
      render(<WalkthroughLink walkthroughId="test-walkthrough" />);

      await waitFor(() => {
        const link = screen.getByRole('link', { name: /view walkthrough: test walkthrough/i });
        expect(link).toHaveAttribute('href', '/walkthroughs/test-walkthrough');
      });
    });

    it('should show only first 4 topics with "+X more" for additional topics', async () => {
      const walkthroughWithManyTopics = {
        ...mockWalkthrough,
        topics: ['Topic1', 'Topic2', 'Topic3', 'Topic4', 'Topic5', 'Topic6'],
      };
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(walkthroughWithManyTopics),
      });

      render(<WalkthroughLink walkthroughId="test-walkthrough" />);

      await waitFor(() => {
        expect(screen.getByText('Topic1')).toBeInTheDocument();
        expect(screen.getByText('Topic2')).toBeInTheDocument();
        expect(screen.getByText('Topic3')).toBeInTheDocument();
        expect(screen.getByText('Topic4')).toBeInTheDocument();
        expect(screen.getByText('+2 more')).toBeInTheDocument();
        expect(screen.queryByText('Topic5')).not.toBeInTheDocument();
      });
    });
  });

  describe('Invalid Walkthrough ID', () => {
    beforeEach(() => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
      });
    });

    it('should render warning message for invalid walkthrough ID', async () => {
      render(<WalkthroughLink walkthroughId="invalid-id" />);

      await waitFor(() => {
        expect(screen.getByText('Walkthrough Not Found')).toBeInTheDocument();
      });
    });

    it('should display the invalid walkthrough ID in the warning', async () => {
      render(<WalkthroughLink walkthroughId="invalid-id" />);

      await waitFor(() => {
        expect(screen.getByText('invalid-id')).toBeInTheDocument();
      });
    });

    it('should render warning with appropriate ARIA attributes', async () => {
      render(<WalkthroughLink walkthroughId="invalid-id" />);

      await waitFor(() => {
        const alert = screen.getByRole('alert');
        expect(alert).toBeInTheDocument();
        expect(alert).toHaveAttribute('aria-live', 'polite');
      });
    });

    it('should not render walkthrough card elements', async () => {
      render(<WalkthroughLink walkthroughId="invalid-id" />);

      await waitFor(() => {
        expect(screen.getByText('Walkthrough Not Found')).toBeInTheDocument();
      });
      expect(screen.queryByText('View Walkthrough')).not.toBeInTheDocument();
      expect(screen.queryByRole('link')).not.toBeInTheDocument();
    });
  });

  describe('Difficulty Variants', () => {
    it('should render Beginner difficulty', async () => {
      const beginnerWalkthrough = { ...mockWalkthrough, difficulty: 'Beginner' as const };
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(beginnerWalkthrough),
      });

      render(<WalkthroughLink walkthroughId="test-walkthrough" />);

      await waitFor(() => {
        expect(screen.getByText('Beginner')).toBeInTheDocument();
      });
    });

    it('should render Advanced difficulty', async () => {
      const advancedWalkthrough = { ...mockWalkthrough, difficulty: 'Advanced' as const };
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(advancedWalkthrough),
      });

      render(<WalkthroughLink walkthroughId="test-walkthrough" />);

      await waitFor(() => {
        expect(screen.getByText('Advanced')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle walkthrough with no topics', async () => {
      const walkthroughNoTopics = { ...mockWalkthrough, topics: [] };
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(walkthroughNoTopics),
      });

      render(<WalkthroughLink walkthroughId="test-walkthrough" />);

      await waitFor(() => {
        expect(screen.getByText('Test Walkthrough')).toBeInTheDocument();
      });
      // Topics section should not be rendered
      expect(screen.queryByText('Testing')).not.toBeInTheDocument();
    });

    it('should handle walkthrough with very long description', async () => {
      const longDescription = 'A'.repeat(500);
      const walkthroughLongDesc = { ...mockWalkthrough, description: longDescription };
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(walkthroughLongDesc),
      });

      render(<WalkthroughLink walkthroughId="test-walkthrough" />);

      await waitFor(() => {
        expect(screen.getByText(longDescription)).toBeInTheDocument();
      });
    });
  });
});
