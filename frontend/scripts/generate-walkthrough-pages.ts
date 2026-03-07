#!/usr/bin/env node

import fs from 'fs';
import path from 'path';

const CONTENT_DIR = path.join(process.cwd(), 'content', 'walkthroughs');
const APP_WALKTHROUGHS_DIR = path.join(process.cwd(), 'app', 'walkthroughs');

console.log('🚀 Generating static walkthrough pages...\n');

interface WalkthroughMetadata {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  topics: string[];
  estimatedTime: number;
  prerequisites: string[];
  repository: string;
}

function generateWalkthroughPage(metadata: WalkthroughMetadata, readmePath: string): string {
  const readme = fs.readFileSync(readmePath, 'utf-8');

  return `/**
 * Static Walkthrough Page: ${metadata.title}
 * Generated from content/walkthroughs/${metadata.id}
 */

import { WalkthroughPageTemplate } from '@/components/WalkthroughPageTemplate';
import { Walkthrough } from '@/lib/types';

const walkthrough: Walkthrough = ${JSON.stringify(metadata, null, 2)} as Walkthrough;

const readme = ${JSON.stringify(readme)};

export default function WalkthroughPage() {
  return <WalkthroughPageTemplate walkthrough={walkthrough} readme={readme} />;
}
`;
}

function main() {
  // Clean existing walkthrough pages (except the index)
  if (fs.existsSync(APP_WALKTHROUGHS_DIR)) {
    const entries = fs.readdirSync(APP_WALKTHROUGHS_DIR, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isDirectory() && entry.name !== 'page.tsx') {
        const dirPath = path.join(APP_WALKTHROUGHS_DIR, entry.name);
        fs.rmSync(dirPath, { recursive: true, force: true });
        console.log(`🗑️  Removed old directory: ${entry.name}`);
      }
    }
  }

  // Read all walkthrough directories
  const entries = fs.readdirSync(CONTENT_DIR, { withFileTypes: true });
  let generatedCount = 0;

  for (const entry of entries) {
    if (!entry.isDirectory() || entry.name.startsWith('.') || entry.name === 'template') {
      continue;
    }

    const walkthroughDir = path.join(CONTENT_DIR, entry.name);
    const metadataPath = path.join(walkthroughDir, 'metadata.json');
    const readmePath = path.join(walkthroughDir, 'README.md');

    // Check if required files exist
    if (!fs.existsSync(metadataPath)) {
      console.warn(`⚠️  Skipping ${entry.name}: metadata.json not found`);
      continue;
    }

    if (!fs.existsSync(readmePath)) {
      console.warn(`⚠️  Skipping ${entry.name}: README.md not found`);
      continue;
    }

    try {
      // Read metadata
      const metadataContent = fs.readFileSync(metadataPath, 'utf-8');
      const metadata: WalkthroughMetadata = JSON.parse(metadataContent);

      // Create directory for this walkthrough
      const pageDir = path.join(APP_WALKTHROUGHS_DIR, metadata.id);
      fs.mkdirSync(pageDir, { recursive: true });

      // Generate page component
      const pageContent = generateWalkthroughPage(metadata, readmePath);
      const pagePath = path.join(pageDir, 'page.tsx');
      fs.writeFileSync(pagePath, pageContent);

      console.log(`✅ Generated: /walkthroughs/${metadata.id}`);
      generatedCount++;
    } catch (error) {
      console.error(`❌ Error processing ${entry.name}:`, error);
    }
  }

  console.log(`\n✨ Generated ${generatedCount} walkthrough pages!`);
}

main();
