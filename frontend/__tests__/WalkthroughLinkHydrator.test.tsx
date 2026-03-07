import { render, waitFor } from '@testing-library/react';
import { WalkthroughLinkHydrator } from '@/components/WalkthroughLinkHydrator';
import * as walkthroughsModule from '@/lib/walkthroughs';

/**
 * Unit tests for WalkthroughLinkHydrator component
 * 
 * Tests the client-side hydration of walkthrough link placeholders
 * that are generated from markdown directives.
 * 
 * Requirements: 9.1, 9.2
 */

// Mock the walkthroughs module
jest.mock('@/lib/walkthroughs', () => ({
  getWalkthroughById: jest.fn(),
}));

describe('WalkthroughLinkHydrator', () => {
  const mockWalkthrough = {
    id: 'test-walkthrough',
    title: 'Test Walkthrough',
    description: 'This is a test walkthrough',
    difficulty: 'Intermediate' as const,
    topics: ['Testing'],
    estimatedTime: 30,
    prerequisites: [],
    repository: 'walkthroughs/test-walkthrough',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // Clear any existing placeholders from previous tests
    document.body.innerHTML = '';
  });

  describe('Placeholder Hydration', () => {
    it('should hydrate a single walkthrough placeholder', async () => {
      // Mock the walkthrough data
      (walkthroughsModule.getWalkthroughById as jest.Mock).mockReturnValue(mockWalkthrough);

      // Create a placeholder in the DOM
      document.body.innerHTML = `
        <div class="walkthrough-link-placeholder" data-walkthrough-id="test-walkthrough"></div>
      `;

      // Render the hydrator
      render(<WalkthroughLinkHydrator />);

      // Wait for hydration to complete
      await waitFor(() => {
        expect(document.body.textContent).toContain('Test Walkthrough');
      });

      // Verify the walkthrough content is rendered
      expect(document.body.textContent).toContain('This is a test walkthrough');
      expect(document.body.textContent).toContain('Intermediate');
    });

    it('should hydrate multiple walkthrough placeholders', async () => {
      // Mock different walkthroughs
      (walkthroughsModule.getWalkthroughById as jest.Mock)
        .mockImplementation((id: string) => {
          if (id === 'first-walkthrough') {
            return { ...mockWalkthrough, id: 'first-walkthrough', title: 'First Walkthrough' };
          }
          if (id === 'second-walkthrough') {
            return { ...mockWalkthrough, id: 'second-walkthrough', title: 'Second Walkthrough' };
          }
          return null;
        });

      // Create multiple placeholders
      document.body.innerHTML = `
        <div class="walkthrough-link-placeholder" data-walkthrough-id="first-walkthrough"></div>
        <div class="walkthrough-link-placeholder" data-walkthrough-id="second-walkthrough"></div>
      `;

      render(<WalkthroughLinkHydrator />);

      // Wait for both to be hydrated
      await waitFor(() => {
        expect(document.body.textContent).toContain('First Walkthrough');
        expect(document.body.textContent).toContain('Second Walkthrough');
      });
    });

    it('should handle invalid walkthrough ID gracefully', async () => {
      // Mock to return null for invalid ID
      (walkthroughsModule.getWalkthroughById as jest.Mock).mockReturnValue(null);

      document.body.innerHTML = `
        <div class="walkthrough-link-placeholder" data-walkthrough-id="invalid-id"></div>
      `;

      render(<WalkthroughLinkHydrator />);

      // Wait for hydration
      await waitFor(() => {
        expect(document.body.textContent).toContain('Walkthrough Not Found');
      });

      expect(document.body.textContent).toContain('invalid-id');
    });

    it('should handle placeholder without data-walkthrough-id attribute', async () => {
      const warnSpy = jest.spyOn(console, 'warn').mockImplementation();

      document.body.innerHTML = `
        <div class="walkthrough-link-placeholder"></div>
      `;

      render(<WalkthroughLinkHydrator />);

      // Should log a warning
      await waitFor(() => {
        expect(warnSpy).toHaveBeenCalledWith('Walkthrough placeholder missing data-walkthrough-id attribute');
      });

      warnSpy.mockRestore();
    });
  });

  describe('Component Behavior', () => {
    it('should not render any visible content itself', () => {
      const { container } = render(<WalkthroughLinkHydrator />);
      
      // The hydrator component itself should not render anything
      expect(container.firstChild).toBeNull();
    });

    it('should only run hydration once on mount', async () => {
      (walkthroughsModule.getWalkthroughById as jest.Mock).mockReturnValue(mockWalkthrough);

      document.body.innerHTML = `
        <div class="walkthrough-link-placeholder" data-walkthrough-id="test-walkthrough"></div>
      `;

      const { rerender } = render(<WalkthroughLinkHydrator />);

      await waitFor(() => {
        expect(document.body.textContent).toContain('Test Walkthrough');
      });

      // Clear the mock call count
      (walkthroughsModule.getWalkthroughById as jest.Mock).mockClear();

      // Rerender the component
      rerender(<WalkthroughLinkHydrator />);

      // Should not call getWalkthroughById again
      expect(walkthroughsModule.getWalkthroughById).not.toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty document with no placeholders', () => {
      document.body.innerHTML = '<div>No placeholders here</div>';

      const { container } = render(<WalkthroughLinkHydrator />);

      // Should not throw errors
      expect(container).toBeTruthy();
    });

    it('should handle placeholder with empty string id', async () => {
      const warnSpy = jest.spyOn(console, 'warn').mockImplementation();

      document.body.innerHTML = `
        <div class="walkthrough-link-placeholder" data-walkthrough-id=""></div>
      `;

      render(<WalkthroughLinkHydrator />);

      // Empty string is falsy, should log warning
      await waitFor(() => {
        expect(warnSpy).toHaveBeenCalled();
      });

      warnSpy.mockRestore();
    });

    it('should handle placeholders nested in other elements', async () => {
      (walkthroughsModule.getWalkthroughById as jest.Mock).mockReturnValue(mockWalkthrough);

      document.body.innerHTML = `
        <div class="prose">
          <p>Some content</p>
          <div class="walkthrough-link-placeholder" data-walkthrough-id="test-walkthrough"></div>
          <p>More content</p>
        </div>
      `;

      render(<WalkthroughLinkHydrator />);

      await waitFor(() => {
        expect(document.body.textContent).toContain('Test Walkthrough');
      });

      // Surrounding content should still be present
      expect(document.body.textContent).toContain('Some content');
      expect(document.body.textContent).toContain('More content');
    });
  });
});
