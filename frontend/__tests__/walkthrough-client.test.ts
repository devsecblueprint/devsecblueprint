import {
  getWalkthroughsWithProgress,
} from '@/lib/walkthrough-client';

// Mock fetch for API calls
global.fetch = jest.fn();

describe('Walkthrough Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getWalkthroughsWithProgress', () => {
    it('should fetch walkthroughs from API', async () => {
      const mockWalkthroughs = [
        {
          id: 'test-walkthrough',
          title: 'Test Walkthrough',
          description: 'Test description',
          difficulty: 'Beginner' as const,
          topics: ['Testing'],
          estimatedTime: 30,
          prerequisites: [],
          repository: 'walkthroughs/test-walkthrough'
        }
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ walkthroughs: mockWalkthroughs })
      });

      // Mock progress API call
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404
      });

      const walkthroughs = await getWalkthroughsWithProgress();
      
      expect(walkthroughs).toBeDefined();
      expect(Array.isArray(walkthroughs)).toBe(true);
      expect(walkthroughs.length).toBeGreaterThan(0);
      expect(walkthroughs[0]).toHaveProperty('progress');
    });
  });

});
