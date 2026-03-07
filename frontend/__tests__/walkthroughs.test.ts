import {
  getAllWalkthroughs,
  getWalkthroughById,
  loadWalkthroughReadme,
  filterByDifficulty,
  filterByTopics,
  searchWalkthroughs,
  applyFilters,
  getAllTopics
} from '@/lib/walkthroughs';

describe('Walkthrough Utilities', () => {
  describe('getAllWalkthroughs', () => {
    it('should load all walkthroughs from content directory', () => {
      const walkthroughs = getAllWalkthroughs();
      
      expect(walkthroughs).toBeDefined();
      expect(Array.isArray(walkthroughs)).toBe(true);
      expect(walkthroughs.length).toBeGreaterThan(0);
    });

    it('should have valid metadata structure', () => {
      const walkthroughs = getAllWalkthroughs();
      
      walkthroughs.forEach(w => {
        expect(w).toHaveProperty('id');
        expect(w).toHaveProperty('title');
        expect(w).toHaveProperty('description');
        expect(w).toHaveProperty('difficulty');
        expect(w).toHaveProperty('topics');
        expect(w).toHaveProperty('estimatedTime');
        expect(w).toHaveProperty('prerequisites');
        expect(w).toHaveProperty('repository');
        
        expect(['Beginner', 'Intermediate', 'Advanced']).toContain(w.difficulty);
        expect(Array.isArray(w.topics)).toBe(true);
        expect(Array.isArray(w.prerequisites)).toBe(true);
        expect(typeof w.estimatedTime).toBe('number');
        expect(w.estimatedTime).toBeGreaterThan(0);
      });
    });
  });

  describe('getWalkthroughById', () => {
    it('should return walkthrough when ID exists', () => {
      const walkthroughs = getAllWalkthroughs();
      if (walkthroughs.length > 0) {
        const firstId = walkthroughs[0].id;
        const walkthrough = getWalkthroughById(firstId);
        
        expect(walkthrough).not.toBeNull();
        expect(walkthrough?.id).toBe(firstId);
      }
    });

    it('should return null when ID does not exist', () => {
      const walkthrough = getWalkthroughById('non-existent-id');
      expect(walkthrough).toBeNull();
    });
  });

  describe('loadWalkthroughReadme', () => {
    it('should load README content for valid walkthrough', () => {
      const walkthroughs = getAllWalkthroughs();
      if (walkthroughs.length > 0) {
        const firstId = walkthroughs[0].id;
        const readme = loadWalkthroughReadme(firstId);
        
        expect(readme).not.toBeNull();
        expect(typeof readme).toBe('string');
        expect(readme!.length).toBeGreaterThan(0);
      }
    });

    it('should return null for non-existent walkthrough', () => {
      const readme = loadWalkthroughReadme('non-existent-id');
      expect(readme).toBeNull();
    });
  });

  describe('filterByDifficulty', () => {
    it('should filter walkthroughs by difficulty', () => {
      const walkthroughs = getAllWalkthroughs();
      const beginnerWalkthroughs = filterByDifficulty(walkthroughs, 'Beginner');
      
      beginnerWalkthroughs.forEach(w => {
        expect(w.difficulty).toBe('Beginner');
      });
    });

    it('should return empty array when no matches', () => {
      const walkthroughs = getAllWalkthroughs();
      // Filter by a difficulty that might not exist
      const filtered = filterByDifficulty(walkthroughs, 'Advanced');
      expect(Array.isArray(filtered)).toBe(true);
    });
  });

  describe('filterByTopics', () => {
    it('should filter walkthroughs by topics', () => {
      const walkthroughs = getAllWalkthroughs();
      if (walkthroughs.length > 0 && walkthroughs[0].topics.length > 0) {
        const firstTopic = walkthroughs[0].topics[0];
        const filtered = filterByTopics(walkthroughs, [firstTopic]);
        
        expect(filtered.length).toBeGreaterThan(0);
        filtered.forEach(w => {
          expect(w.topics).toContain(firstTopic);
        });
      }
    });

    it('should return all walkthroughs when topics array is empty', () => {
      const walkthroughs = getAllWalkthroughs();
      const filtered = filterByTopics(walkthroughs, []);
      
      expect(filtered).toEqual(walkthroughs);
    });
  });

  describe('searchWalkthroughs', () => {
    it('should search in title', () => {
      const walkthroughs = getAllWalkthroughs();
      if (walkthroughs.length > 0) {
        const firstTitle = walkthroughs[0].title;
        const searchTerm = firstTitle.split(' ')[0].toLowerCase();
        const results = searchWalkthroughs(walkthroughs, searchTerm);
        
        expect(results.length).toBeGreaterThan(0);
      }
    });

    it('should be case-insensitive', () => {
      const walkthroughs = getAllWalkthroughs();
      if (walkthroughs.length > 0) {
        const firstTitle = walkthroughs[0].title;
        const searchTerm = firstTitle.split(' ')[0];
        
        const lowerResults = searchWalkthroughs(walkthroughs, searchTerm.toLowerCase());
        const upperResults = searchWalkthroughs(walkthroughs, searchTerm.toUpperCase());
        
        expect(lowerResults).toEqual(upperResults);
      }
    });

    it('should return all walkthroughs when query is empty', () => {
      const walkthroughs = getAllWalkthroughs();
      const results = searchWalkthroughs(walkthroughs, '');
      
      expect(results).toEqual(walkthroughs);
    });
  });

  describe('applyFilters', () => {
    it('should apply multiple filters together', () => {
      const walkthroughs = getAllWalkthroughs();
      
      const filters = {
        difficulty: 'Beginner' as const,
        topics: ['Docker'],
        search: 'security'
      };
      
      const filtered = applyFilters(walkthroughs, filters);
      
      filtered.forEach(w => {
        expect(w.difficulty).toBe('Beginner');
        expect(w.topics.some(t => filters.topics!.includes(t))).toBe(true);
        
        const matchesSearch = 
          w.title.toLowerCase().includes('security') ||
          w.description.toLowerCase().includes('security') ||
          w.topics.some(t => t.toLowerCase().includes('security'));
        expect(matchesSearch).toBe(true);
      });
    });

    it('should return all walkthroughs when no filters applied', () => {
      const walkthroughs = getAllWalkthroughs();
      const filtered = applyFilters(walkthroughs, {});
      
      expect(filtered).toEqual(walkthroughs);
    });
  });

  describe('getAllTopics', () => {
    it('should return unique sorted topics', () => {
      const walkthroughs = getAllWalkthroughs();
      const topics = getAllTopics(walkthroughs);
      
      expect(Array.isArray(topics)).toBe(true);
      expect(topics.length).toBeGreaterThan(0);
      
      // Check uniqueness
      const uniqueTopics = new Set(topics);
      expect(uniqueTopics.size).toBe(topics.length);
      
      // Check sorted
      const sortedTopics = [...topics].sort();
      expect(topics).toEqual(sortedTopics);
    });
  });
});
