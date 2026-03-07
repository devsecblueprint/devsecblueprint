#!/usr/bin/env tsx
/**
 * Compare Walkthrough Registries
 * 
 * This script compares walkthrough entries from:
 * 1. The generated content-registry.json (parsed from README.md files)
 * 2. The hardcoded metadata.json files (used by backend/services/walkthrough_registry.py)
 * 
 * Purpose: Verify migration compatibility for Task 19.2
 */

import * as fs from 'fs';
import * as path from 'path';

interface WalkthroughEntry {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  topics: string[];
  estimated_time: number;
  prerequisites: string[];
  repository: string;
}

interface ContentRegistry {
  entries: {
    [key: string]: {
      content_type: string;
      id?: string;
      title?: string;
      description?: string;
      difficulty?: string;
      topics?: string[];
      estimated_time?: number;
      prerequisites?: string[];
      repository?: string;
    };
  };
}

interface MetadataJson {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  topics: string[];
  estimatedTime: number;
  prerequisites: string[];
  repository: string;
}

function loadGeneratedRegistry(): Map<string, WalkthroughEntry> {
  const registryPath = path.join(process.cwd(), 'content-registry.json');
  const registry: ContentRegistry = JSON.parse(fs.readFileSync(registryPath, 'utf-8'));
  
  const walkthroughs = new Map<string, WalkthroughEntry>();
  
  for (const [key, entry] of Object.entries(registry.entries)) {
    if (entry.content_type === 'walkthrough') {
      walkthroughs.set(entry.id!, {
        id: entry.id!,
        title: entry.title!,
        description: entry.description!,
        difficulty: entry.difficulty!,
        topics: entry.topics!,
        estimated_time: entry.estimated_time!,
        prerequisites: entry.prerequisites!,
        repository: entry.repository!,
      });
    }
  }
  
  return walkthroughs;
}

function loadMetadataFiles(): Map<string, WalkthroughEntry> {
  const walkthroughsDir = path.join(process.cwd(), 'content', 'walkthroughs');
  const walkthroughs = new Map<string, WalkthroughEntry>();
  
  const dirs = fs.readdirSync(walkthroughsDir, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .filter(dirent => dirent.name !== 'template'); // Skip template
  
  for (const dir of dirs) {
    const metadataPath = path.join(walkthroughsDir, dir.name, 'metadata.json');
    
    if (fs.existsSync(metadataPath)) {
      const metadata: MetadataJson = JSON.parse(fs.readFileSync(metadataPath, 'utf-8'));
      
      walkthroughs.set(metadata.id, {
        id: metadata.id,
        title: metadata.title,
        description: metadata.description,
        difficulty: metadata.difficulty,
        topics: metadata.topics,
        estimated_time: metadata.estimatedTime,
        prerequisites: metadata.prerequisites,
        repository: metadata.repository,
      });
    }
  }
  
  return walkthroughs;
}

function compareWalkthroughs(
  generated: Map<string, WalkthroughEntry>,
  metadata: Map<string, WalkthroughEntry>
): void {
  console.log('=== Walkthrough Registry Comparison ===\n');
  
  console.log(`Generated registry entries: ${generated.size}`);
  console.log(`Metadata.json files: ${metadata.size}\n`);
  
  // Check for missing walkthroughs
  const generatedIds = new Set(generated.keys());
  const metadataIds = new Set(metadata.keys());
  
  const onlyInGenerated = [...generatedIds].filter(id => !metadataIds.has(id));
  const onlyInMetadata = [...metadataIds].filter(id => !generatedIds.has(id));
  
  if (onlyInGenerated.length > 0) {
    console.log('⚠️  Walkthroughs only in generated registry:');
    onlyInGenerated.forEach(id => console.log(`   - ${id}`));
    console.log();
  }
  
  if (onlyInMetadata.length > 0) {
    console.log('⚠️  Walkthroughs only in metadata.json files:');
    onlyInMetadata.forEach(id => console.log(`   - ${id}`));
    console.log();
  }
  
  // Compare common walkthroughs
  const commonIds = [...generatedIds].filter(id => metadataIds.has(id));
  
  console.log(`\n=== Comparing ${commonIds.length} Common Walkthroughs ===\n`);
  
  let totalDifferences = 0;
  
  for (const id of commonIds) {
    const gen = generated.get(id)!;
    const meta = metadata.get(id)!;
    
    const differences: string[] = [];
    
    // Compare each field
    if (gen.title !== meta.title) {
      differences.push(`  Title: "${gen.title}" vs "${meta.title}"`);
    }
    
    if (gen.description !== meta.description) {
      differences.push(`  Description differs (lengths: ${gen.description.length} vs ${meta.description.length})`);
    }
    
    if (gen.difficulty !== meta.difficulty) {
      differences.push(`  Difficulty: "${gen.difficulty}" vs "${meta.difficulty}"`);
    }
    
    if (gen.estimated_time !== meta.estimated_time) {
      differences.push(`  Estimated time: ${gen.estimated_time} vs ${meta.estimated_time}`);
    }
    
    if (JSON.stringify(gen.prerequisites) !== JSON.stringify(meta.prerequisites)) {
      differences.push(`  Prerequisites: ${JSON.stringify(gen.prerequisites)} vs ${JSON.stringify(meta.prerequisites)}`);
    }
    
    if (gen.repository !== meta.repository) {
      differences.push(`  Repository: "${gen.repository}" vs "${meta.repository}"`);
    }
    
    // Compare topics (order-independent)
    const genTopics = new Set(gen.topics.map(t => t.toLowerCase()));
    const metaTopics = new Set(meta.topics.map(t => t.toLowerCase()));
    
    const topicsMatch = genTopics.size === metaTopics.size && 
                        [...genTopics].every(t => metaTopics.has(t));
    
    if (!topicsMatch) {
      differences.push(`  Topics: [${gen.topics.join(', ')}] vs [${meta.topics.join(', ')}]`);
    }
    
    if (differences.length > 0) {
      console.log(`❌ ${id}:`);
      differences.forEach(diff => console.log(diff));
      console.log();
      totalDifferences += differences.length;
    } else {
      console.log(`✓ ${id}: All fields match`);
    }
  }
  
  console.log(`\n=== Summary ===`);
  console.log(`Total walkthroughs compared: ${commonIds.length}`);
  console.log(`Total field differences: ${totalDifferences}`);
  console.log(`Walkthroughs only in generated: ${onlyInGenerated.length}`);
  console.log(`Walkthroughs only in metadata: ${onlyInMetadata.length}`);
  
  if (totalDifferences === 0 && onlyInGenerated.length === 0 && onlyInMetadata.length === 0) {
    console.log('\n✓ Perfect match! All walkthroughs are identical.');
  } else {
    console.log('\n⚠️  Discrepancies found. Review differences above.');
  }
}

// Main execution
try {
  const generated = loadGeneratedRegistry();
  const metadata = loadMetadataFiles();
  
  compareWalkthroughs(generated, metadata);
} catch (error) {
  console.error('Error comparing registries:', error);
  process.exit(1);
}
