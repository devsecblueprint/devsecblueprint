import fs from 'fs';
import path from 'path';
import { Walkthrough } from '@/lib/types';

const WALKTHROUGHS_DIR = path.join(process.cwd(), 'content', 'walkthroughs');

/**
 * Validate walkthrough metadata structure
 */
function validateMetadata(data: any, walkthroughId: string): boolean {
  const requiredFields = [
    'id', 'title', 'description', 'difficulty', 
    'topics', 'estimatedTime', 'prerequisites', 'repository'
  ];
  
  for (const field of requiredFields) {
    if (!(field in data)) {
      console.warn(`Walkthrough ${walkthroughId}: Missing required field "${field}"`);
      return false;
    }
  }
  
  // Validate difficulty
  const validDifficulties = ['Beginner', 'Intermediate', 'Advanced'];
  if (!validDifficulties.includes(data.difficulty)) {
    console.warn(`Walkthrough ${walkthroughId}: Invalid difficulty "${data.difficulty}"`);
    return false;
  }
  
  // Validate types
  if (!Array.isArray(data.topics)) {
    console.warn(`Walkthrough ${walkthroughId}: topics must be an array`);
    return false;
  }
  
  if (!Array.isArray(data.prerequisites)) {
    console.warn(`Walkthrough ${walkthroughId}: prerequisites must be an array`);
    return false;
  }
  
  if (typeof data.estimatedTime !== 'number' || data.estimatedTime <= 0) {
    console.warn(`Walkthrough ${walkthroughId}: estimatedTime must be a positive number`);
    return false;
  }
  
  return true;
}

/**
 * Get all walkthroughs from the content directory
 * This runs at build time or server-side
 */
export function getAllWalkthroughs(): Walkthrough[] {
  const walkthroughs: Walkthrough[] = [];
  
  try {
    // Read all directories in walkthroughs folder
    const entries = fs.readdirSync(WALKTHROUGHS_DIR, { withFileTypes: true });
    
    for (const entry of entries) {
      // Skip files and special directories
      if (!entry.isDirectory() || entry.name.startsWith('.') || entry.name === 'template') {
        continue;
      }
      
      const walkthroughPath = path.join(WALKTHROUGHS_DIR, entry.name);
      const metadataPath = path.join(walkthroughPath, 'metadata.json');
      
      // Check if metadata.json exists
      if (!fs.existsSync(metadataPath)) {
        console.warn(`Walkthrough ${entry.name}: metadata.json not found`);
        continue;
      }
      
      try {
        // Read and parse metadata
        const metadataContent = fs.readFileSync(metadataPath, 'utf-8');
        const metadata = JSON.parse(metadataContent);
        
        // Validate metadata
        if (!validateMetadata(metadata, entry.name)) {
          continue;
        }
        
        walkthroughs.push({
          id: metadata.id,
          title: metadata.title,
          description: metadata.description,
          difficulty: metadata.difficulty,
          topics: metadata.topics,
          estimatedTime: metadata.estimatedTime,
          prerequisites: metadata.prerequisites,
          repository: metadata.repository
        });
      } catch (error) {
        console.warn(`Walkthrough ${entry.name}: Failed to parse metadata.json`, error);
        continue;
      }
    }
  } catch (error) {
    console.error('Failed to read walkthroughs directory:', error);
  }
  
  return walkthroughs;
}

/**
 * Get a single walkthrough by ID
 */
export function getWalkthroughById(id: string): Walkthrough | null {
  const walkthroughs = getAllWalkthroughs();
  return walkthroughs.find(w => w.id === id) || null;
}

/**
 * Load README content for a walkthrough
 */
export function loadWalkthroughReadme(id: string): string | null {
  try {
    // Find the walkthrough directory by checking metadata.json files
    const entries = fs.readdirSync(WALKTHROUGHS_DIR, { withFileTypes: true });
    
    for (const entry of entries) {
      if (!entry.isDirectory() || entry.name.startsWith('.') || entry.name === 'template') {
        continue;
      }
      
      const metadataPath = path.join(WALKTHROUGHS_DIR, entry.name, 'metadata.json');
      
      if (!fs.existsSync(metadataPath)) {
        continue;
      }
      
      try {
        const metadataContent = fs.readFileSync(metadataPath, 'utf-8');
        const metadata = JSON.parse(metadataContent);
        
        // Check if this is the walkthrough we're looking for
        if (metadata.id === id) {
          const readmePath = path.join(WALKTHROUGHS_DIR, entry.name, 'README.md');
          
          if (!fs.existsSync(readmePath)) {
            console.warn(`Walkthrough ${id}: README.md not found in ${entry.name}`);
            return null;
          }
          
          return fs.readFileSync(readmePath, 'utf-8');
        }
      } catch (error) {
        console.warn(`Failed to parse metadata for ${entry.name}:`, error);
        continue;
      }
    }
    
    console.warn(`Walkthrough ${id}: No matching directory found`);
    return null;
  } catch (error) {
    console.error(`Failed to load README for walkthrough ${id}:`, error);
    return null;
  }
}

/**
 * Filter walkthroughs by difficulty
 */
export function filterByDifficulty(
  walkthroughs: Walkthrough[],
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced'
): Walkthrough[] {
  return walkthroughs.filter(w => w.difficulty === difficulty);
}

/**
 * Filter walkthroughs by topics (OR logic - matches any topic)
 */
export function filterByTopics(
  walkthroughs: Walkthrough[],
  topics: string[]
): Walkthrough[] {
  if (topics.length === 0) {
    return walkthroughs;
  }
  
  return walkthroughs.filter(w =>
    w.topics.some(topic => topics.includes(topic))
  );
}

/**
 * Search walkthroughs by query (case-insensitive, partial match)
 * Searches in title, description, and topics
 */
export function searchWalkthroughs(
  walkthroughs: Walkthrough[],
  query: string
): Walkthrough[] {
  if (!query || query.trim() === '') {
    return walkthroughs;
  }
  
  const lowerQuery = query.toLowerCase();
  
  return walkthroughs.filter(w => {
    const titleMatch = w.title.toLowerCase().includes(lowerQuery);
    const descMatch = w.description.toLowerCase().includes(lowerQuery);
    const topicMatch = w.topics.some(topic => 
      topic.toLowerCase().includes(lowerQuery)
    );
    
    return titleMatch || descMatch || topicMatch;
  });
}

/**
 * Apply multiple filters to walkthroughs
 */
export function applyFilters(
  walkthroughs: Walkthrough[],
  filters: {
    difficulty?: 'Beginner' | 'Intermediate' | 'Advanced';
    topics?: string[];
    search?: string;
  }
): Walkthrough[] {
  let filtered = walkthroughs;
  
  // Apply difficulty filter
  if (filters.difficulty) {
    filtered = filterByDifficulty(filtered, filters.difficulty);
  }
  
  // Apply topic filter
  if (filters.topics && filters.topics.length > 0) {
    filtered = filterByTopics(filtered, filters.topics);
  }
  
  // Apply search
  if (filters.search) {
    filtered = searchWalkthroughs(filtered, filters.search);
  }
  
  return filtered;
}

/**
 * Get all unique topics from walkthroughs
 */
export function getAllTopics(walkthroughs: Walkthrough[]): string[] {
  const topicsSet = new Set<string>();
  
  walkthroughs.forEach(w => {
    w.topics.forEach(topic => topicsSet.add(topic));
  });
  
  return Array.from(topicsSet).sort();
}
