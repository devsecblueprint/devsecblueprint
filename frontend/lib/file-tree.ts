import fs from 'fs';
import path from 'path';
import type { FileNode } from '@/components/FileBrowser';

const WALKTHROUGHS_DIR = path.join(process.cwd(), 'content', 'walkthroughs');

/**
 * Build a file tree for a walkthrough directory
 * 
 * @param walkthroughId - The walkthrough identifier
 * @returns Array of file nodes representing the directory structure
 */
export function buildFileTree(walkthroughId: string): FileNode[] {
  const walkthroughPath = path.join(WALKTHROUGHS_DIR, walkthroughId);
  
  if (!fs.existsSync(walkthroughPath)) {
    return [];
  }
  
  return buildTreeRecursive(walkthroughPath, '');
}

/**
 * Recursively build file tree structure
 * 
 * @param dirPath - Absolute path to directory
 * @param relativePath - Relative path from walkthrough root
 * @returns Array of file nodes
 */
function buildTreeRecursive(dirPath: string, relativePath: string): FileNode[] {
  const nodes: FileNode[] = [];
  
  try {
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });
    
    // Sort: directories first, then files, alphabetically
    entries.sort((a, b) => {
      if (a.isDirectory() && !b.isDirectory()) return -1;
      if (!a.isDirectory() && b.isDirectory()) return 1;
      return a.name.localeCompare(b.name);
    });
    
    for (const entry of entries) {
      // Skip hidden files and special files
      if (entry.name.startsWith('.') || entry.name === 'metadata.json' || entry.name === 'README.md') {
        continue;
      }
      
      const entryPath = path.join(dirPath, entry.name);
      const entryRelativePath = relativePath ? `${relativePath}/${entry.name}` : entry.name;
      
      if (entry.isDirectory()) {
        const children = buildTreeRecursive(entryPath, entryRelativePath);
        nodes.push({
          name: entry.name,
          path: entryRelativePath,
          type: 'directory',
          children
        });
      } else {
        nodes.push({
          name: entry.name,
          path: entryRelativePath,
          type: 'file'
        });
      }
    }
  } catch (error) {
    console.error(`Error reading directory ${dirPath}:`, error);
  }
  
  return nodes;
}

/**
 * Read file content from a walkthrough directory
 * 
 * @param walkthroughId - The walkthrough identifier
 * @param filePath - Relative path to the file within the walkthrough
 * @returns File content as string, or null if not found
 */
export function readWalkthroughFile(walkthroughId: string, filePath: string): string | null {
  try {
    const fullPath = path.join(WALKTHROUGHS_DIR, walkthroughId, filePath);
    
    // Security check: ensure the resolved path is within the walkthrough directory
    const walkthroughPath = path.join(WALKTHROUGHS_DIR, walkthroughId);
    if (!fullPath.startsWith(walkthroughPath)) {
      console.warn(`Attempted to access file outside walkthrough directory: ${filePath}`);
      return null;
    }
    
    if (!fs.existsSync(fullPath)) {
      return null;
    }
    
    return fs.readFileSync(fullPath, 'utf-8');
  } catch (error) {
    console.error(`Error reading file ${filePath} from walkthrough ${walkthroughId}:`, error);
    return null;
  }
}
