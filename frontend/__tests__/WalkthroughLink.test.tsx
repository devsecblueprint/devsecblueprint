import { render, screen } from '@testing-library/react';
import { WalkthroughLink } from '@/components/WalkthroughLink';
import * as walkthroughsModule from '@/lib/walkthroughs';

// Mock the walkthroughs module
jest.mock('@/lib/walkthroughs', () => ({
  getWalkthroughById: jest.fn(),
}));

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
      (walkthroughsModule.getWalkthroughById as jest.Mock).mockReturnValue(mockWalkthrough);
    });

    it('should render walkthrough card with title', () => {
      render(<WalkthroughLink walkthroughId="test-walkthrough" />);
      
      expect(screen.getByText('Test Walkthrough')).toBeInTheDocument();
    });

    it('should render walkthrough description', () => {
      render(<WalkthroughLink walkthroughId="test-walkthrough" />);
      
      expect(screen.getByText('This is a test walkthrough for unit testing')).toBeInTheDocument();
    });

    it('should render difficulty badge', () => {
      render(<WalkthroughLink walkthroughId="test-walkthrough" />);
      
      expect(screen.getByText('Intermediate')).toBeInTheDocument();
    });

    it('should render estimated time', () => {
      render(<WalkthroughLink walkthroughId="test-walkthrough" />);
      
      expect(screen.getByText('45 minutes')).toBeInTheDocument();
    });

    it('should render topics', () => {
      render(<WalkthroughLink walkthroughId="test-walkthrough" />);
      
      expect(screen.getByText('Testing')).toBeInTheDocument();
      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('TypeScript')).toBeInTheDocument();
    });

    it('should render "View Walkthrough" call to action', () => {
      render(<WalkthroughLink walkthroughId="test-walkthrough" />);
      
      expect(screen.getByText('View Walkthrough')).toBeInTheDocument();
    });

    it('should have link to walkthrough detail page', () => {
      render(<WalkthroughLink walkthroughId="test-walkthrough" />);
      
      const link = screen.getByRole('link', { name: /view walkthrough: test walkthrough/i });
      expect(link).toHaveAttribute('href', '/walkthroughs/test-walkthrough');
    });

    it('should show only first 4 topics with "+X more" for additional topics', () => {
      const walkthroughWithManyTopics = {
        ...mockWalkthrough,
        topics: ['Topic1', 'Topic2', 'Topic3', 'Topic4', 'Topic5', 'Topic6'],
      };
      (walkthroughsModule.getWalkthroughById as jest.Mock).mockReturnValue(walkthroughWithManyTopics);

      render(<WalkthroughLink walkthroughId="test-walkthrough" />);
      
      expect(screen.getByText('Topic1')).toBeInTheDocument();
      expect(screen.getByText('Topic2')).toBeInTheDocument();
      expect(screen.getByText('Topic3')).toBeInTheDocument();
      expect(screen.getByText('Topic4')).toBeInTheDocument();
      expect(screen.getByText('+2 more')).toBeInTheDocument();
      expect(screen.queryByText('Topic5')).not.toBeInTheDocument();
    });
  });

  describe('Invalid Walkthrough ID', () => {
    beforeEach(() => {
      (walkthroughsModule.getWalkthroughById as jest.Mock).mockReturnValue(null);
    });

    it('should render warning message for invalid walkthrough ID', () => {
      render(<WalkthroughLink walkthroughId="invalid-id" />);
      
      expect(screen.getByText('Walkthrough Not Found')).toBeInTheDocument();
    });

    it('should display the invalid walkthrough ID in the warning', () => {
      render(<WalkthroughLink walkthroughId="invalid-id" />);
      
      expect(screen.getByText('invalid-id')).toBeInTheDocument();
    });

    it('should render warning with appropriate ARIA attributes', () => {
      render(<WalkthroughLink walkthroughId="invalid-id" />);
      
      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
      expect(alert).toHaveAttribute('aria-live', 'polite');
    });

    it('should not render walkthrough card elements', () => {
      render(<WalkthroughLink walkthroughId="invalid-id" />);
      
      expect(screen.queryByText('View Walkthrough')).not.toBeInTheDocument();
      expect(screen.queryByRole('link')).not.toBeInTheDocument();
    });
  });

  describe('Difficulty Variants', () => {
    it('should render Beginner difficulty', () => {
      const beginnerWalkthrough = { ...mockWalkthrough, difficulty: 'Beginner' as const };
      (walkthroughsModule.getWalkthroughById as jest.Mock).mockReturnValue(beginnerWalkthrough);

      render(<WalkthroughLink walkthroughId="test-walkthrough" />);
      
      expect(screen.getByText('Beginner')).toBeInTheDocument();
    });

    it('should render Advanced difficulty', () => {
      const advancedWalkthrough = { ...mockWalkthrough, difficulty: 'Advanced' as const };
      (walkthroughsModule.getWalkthroughById as jest.Mock).mockReturnValue(advancedWalkthrough);

      render(<WalkthroughLink walkthroughId="test-walkthrough" />);
      
      expect(screen.getByText('Advanced')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle walkthrough with no topics', () => {
      const walkthroughNoTopics = { ...mockWalkthrough, topics: [] };
      (walkthroughsModule.getWalkthroughById as jest.Mock).mockReturnValue(walkthroughNoTopics);

      render(<WalkthroughLink walkthroughId="test-walkthrough" />);
      
      expect(screen.getByText('Test Walkthrough')).toBeInTheDocument();
      // Topics section should not be rendered
      expect(screen.queryByText('Testing')).not.toBeInTheDocument();
    });

    it('should handle walkthrough with very long description', () => {
      const longDescription = 'A'.repeat(500);
      const walkthroughLongDesc = { ...mockWalkthrough, description: longDescription };
      (walkthroughsModule.getWalkthroughById as jest.Mock).mockReturnValue(walkthroughLongDesc);

      render(<WalkthroughLink walkthroughId="test-walkthrough" />);
      
      // Description should be rendered (line-clamp-2 will handle truncation visually)
      expect(screen.getByText(longDescription)).toBeInTheDocument();
    });
  });
});
