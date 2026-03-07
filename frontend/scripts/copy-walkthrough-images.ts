#!/usr/bin/env node

import fs from 'fs';
import path from 'path';

const CONTENT_DIR = path.join(process.cwd(), 'content', 'walkthroughs');
const PUBLIC_DIR = path.join(process.cwd(), 'public', 'walkthroughs');

console.log('📸 Copying walkthrough images...\n');

interface WalkthroughMetadata {
  id: string;
  title: string;
}

function copyDirectory(src: string, dest: string) {
  // Create destination directory if it doesn't exist
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }

  const entries = fs.readdirSync(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      copyDirectory(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function main() {
  // Clean existing walkthrough images in public
  if (fs.existsSync(PUBLIC_DIR)) {
    fs.rmSync(PUBLIC_DIR, { recursive: true, force: true });
    console.log('🗑️  Cleaned old walkthrough images');
  }

  // Create public/walkthroughs directory
  fs.mkdirSync(PUBLIC_DIR, { recursive: true });

  // Read all walkthrough directories
  const entries = fs.readdirSync(CONTENT_DIR, { withFileTypes: true });
  let copiedCount = 0;

  for (const entry of entries) {
    if (!entry.isDirectory() || entry.name.startsWith('.') || entry.name === 'template') {
      continue;
    }

    const walkthroughDir = path.join(CONTENT_DIR, entry.name);
    const metadataPath = path.join(walkthroughDir, 'metadata.json');
    const imagesDir = path.join(walkthroughDir, 'images');

    // Check if metadata exists
    if (!fs.existsSync(metadataPath)) {
      console.warn(`⚠️  Skipping ${entry.name}: metadata.json not found`);
      continue;
    }

    // Read metadata to get the ID
    const metadataContent = fs.readFileSync(metadataPath, 'utf-8');
    const metadata: WalkthroughMetadata = JSON.parse(metadataContent);

    // Check if images directory exists
    if (fs.existsSync(imagesDir)) {
      // Use the metadata ID for the destination path
      const destDir = path.join(PUBLIC_DIR, metadata.id, 'images');
      copyDirectory(imagesDir, destDir);
      console.log(`✅ Copied images for: ${metadata.id} (from ${entry.name})`);
      copiedCount++;
    }
  }

  if (copiedCount === 0) {
    console.log('ℹ️  No walkthrough images found to copy');
  } else {
    console.log(`\n✨ Copied images from ${copiedCount} walkthrough(s)!`);
  }
}

main();
