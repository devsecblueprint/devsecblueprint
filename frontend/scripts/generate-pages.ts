#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkDirective from 'remark-directive';
import remarkGfm from 'remark-gfm';
import remarkRehype from 'remark-rehype';
import rehypeHighlight from 'rehype-highlight';
import rehypeStringify from 'rehype-stringify';
import { visit } from 'unist-util-visit';

// Types
interface FrontMatter {
  id: string;
  title: string;
  description: string;
  sidebar_position: number;
}

interface Section {
  id: string;
  slug: string;
  title: string;
  description: string;
  sidebar_position: number;
  filePath: string;
  content: string;
  html: string;
}

interface TopicMetadata {
  title: string;
  order: number;
  description?: string;
  type?: 'capstone' | 'standard';
}

interface LearningPathMetadata {
  title: string;
  order: number;
  description?: string;
}

interface Topic {
  slug: string;
  sections: Section[];
  metadata?: TopicMetadata;
}

interface LearningPath {
  topics: { [topic: string]: Topic };
  metadata?: LearningPathMetadata;
}

interface ContentMap {
  [learningPath: string]: LearningPath;
}

// Configuration
const CONTENT_DIR = path.join(process.cwd(), 'content');
const APP_LEARN_DIR = path.join(process.cwd(), 'app', 'learn');
const DATA_DIR = path.join(process.cwd(), 'lib', 'data');

console.log('🚀 Starting markdown to TSX generation...\n');

// Custom plugin to handle :::note directives
function remarkAdmonitions() {
  return (tree: any) => {
    visit(tree, (node) => {
      if (
        node.type === 'containerDirective' ||
        node.type === 'leafDirective'
      ) {
        // Only process containerDirective and leafDirective, NOT textDirective
        // This prevents "2:00" from being treated as a directive
        const data = node.data || (node.data = {});
        const tagName = 'div';

        data.hName = tagName;
        data.hProperties = {
          className: `admonition admonition-${node.name} alert alert--${node.name}`,
          'data-admonition': node.name
        };

        // Capitalize the admonition type for display
        const titleText = node.name.charAt(0).toUpperCase() + node.name.slice(1);

        // Add title element at the beginning with the type name (no icon in markdown, will be added via CSS)
        node.children.unshift({
          type: 'paragraph',
          data: {
            hName: 'div',
            hProperties: { className: 'admonition-heading' }
          },
          children: [
            {
              type: 'heading',
              depth: 5,
              data: {
                hProperties: { className: 'admonition-heading-title' }
              },
              children: [
                {
                  type: 'text',
                  value: titleText
                }
              ]
            }
          ]
        });
      }
    });
  };
}

// Custom plugin to handle :::walkthrough{id="..."} directives
function remarkWalkthroughLinks() {
  return (tree: any) => {
    visit(tree, (node) => {
      if (
        (node.type === 'containerDirective' || node.type === 'leafDirective') &&
        node.name === 'walkthrough'
      ) {
        // Extract the id attribute from the directive
        const walkthroughId = node.attributes?.id;
        
        if (!walkthroughId) {
          console.warn('⚠️  Walkthrough directive missing id attribute');
          return;
        }

        // Transform the node into a custom HTML element that will be replaced client-side
        const data = node.data || (node.data = {});
        data.hName = 'div';
        data.hProperties = {
          className: 'walkthrough-link-placeholder',
          'data-walkthrough-id': walkthroughId
        };

        // Clear children since we'll render the component client-side
        node.children = [];
      }
    });
  };
}

// Convert markdown to HTML with support for directives
async function convertMarkdownToHtml(markdown: string): Promise<string> {
  const result = await unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkDirective)
    .use(remarkAdmonitions)
    .use(remarkWalkthroughLinks)
    .use(remarkRehype, { allowDangerousHtml: true }) // Allow raw HTML like iframes
    .use(rehypeHighlight)
    .use(rehypeStringify, { allowDangerousHtml: true }) // Preserve raw HTML in output
    .process(markdown);

  return String(result);
}

// Read topic metadata from _meta.json file
function readTopicMetadata(topicDir: string): TopicMetadata | undefined {
  const metaPath = path.join(topicDir, '_meta.json');
  
  if (!fs.existsSync(metaPath)) {
    return undefined;  // No metadata file, use defaults
  }
  
  try {
    const content = fs.readFileSync(metaPath, 'utf8');
    const metadata = JSON.parse(content) as TopicMetadata;
    
    // Validate required fields
    if (!metadata.title || typeof metadata.title !== 'string') {
      console.warn(`   ⚠️  Invalid metadata in ${metaPath}: missing or invalid 'title'`);
      return undefined;
    }
    
    if (typeof metadata.order !== 'number') {
      console.warn(`   ⚠️  Invalid metadata in ${metaPath}: missing or invalid 'order'`);
      return undefined;
    }
    
    return metadata;
  } catch (error) {
    console.error(`   ❌ Error reading metadata from ${metaPath}:`, error);
    return undefined;
  }
}

// Read learning path metadata from _meta.json file
function readLearningPathMetadata(learningPathDir: string): LearningPathMetadata | undefined {
  const metaPath = path.join(learningPathDir, '_meta.json');
  
  if (!fs.existsSync(metaPath)) {
    return undefined;  // No metadata file, use defaults
  }
  
  try {
    const content = fs.readFileSync(metaPath, 'utf8');
    const metadata = JSON.parse(content) as LearningPathMetadata;
    
    // Validate required fields
    if (!metadata.title || typeof metadata.title !== 'string') {
      console.warn(`   ⚠️  Invalid metadata in ${metaPath}: missing or invalid 'title'`);
      return undefined;
    }
    
    if (typeof metadata.order !== 'number') {
      console.warn(`   ⚠️  Invalid metadata in ${metaPath}: missing or invalid 'order'`);
      return undefined;
    }
    
    return metadata;
  } catch (error) {
    console.error(`   ❌ Error reading metadata from ${metaPath}:`, error);
    return undefined;
  }
}

// Step 1: Scan content directory
async function scanContentDirectory(): Promise<ContentMap> {
  console.log('📂 Scanning content directory...');
  
  const contentMap: ContentMap = {};
  
  if (!fs.existsSync(CONTENT_DIR)) {
    console.error('❌ Content directory not found:', CONTENT_DIR);
    process.exit(1);
  }
  
  // Get all learning paths (top-level directories), excluding walkthroughs
  const learningPaths = fs.readdirSync(CONTENT_DIR).filter(item => {
    const itemPath = path.join(CONTENT_DIR, item);
    return fs.statSync(itemPath).isDirectory() && item !== 'walkthroughs';
  });
  
  console.log(`   Found ${learningPaths.length} learning paths: ${learningPaths.join(', ')}`);
  
  for (const learningPath of learningPaths) {
    const learningPathDir = path.join(CONTENT_DIR, learningPath);
    
    // Read learning path metadata
    const learningPathMetadata = readLearningPathMetadata(learningPathDir);
    
    contentMap[learningPath] = {
      topics: {},
      metadata: learningPathMetadata
    };
    
    // Get all topics (subdirectories)
    const topics = fs.readdirSync(learningPathDir).filter(item => {
      const itemPath = path.join(learningPathDir, item);
      return fs.statSync(itemPath).isDirectory();
    });
    
    // Check for markdown files directly in the learning path directory (excluding quiz.md)
    const directMarkdownFiles = fs.readdirSync(learningPathDir).filter(file => 
      file.endsWith('.md') && file !== '_meta.json' && file !== 'quiz.md'
    );
    
    // If there are direct markdown files, treat the learning path itself as a topic
    if (directMarkdownFiles.length > 0) {
      const sections: Section[] = [];
      
      for (const file of directMarkdownFiles) {
        const filePath = path.join(learningPathDir, file);
        const fileContents = fs.readFileSync(filePath, 'utf8');
        
        try {
          const { data, content } = matter(fileContents);
          const frontmatter = data as FrontMatter;
          
          // Validate required fields
          if (!frontmatter.id || !frontmatter.title || !frontmatter.description || frontmatter.sidebar_position === undefined) {
            console.error(`   ❌ ERROR: ${file} is missing required frontmatter fields`);
            console.error(`      Required: id, title, description, sidebar_position`);
            console.error(`      Found: ${JSON.stringify(frontmatter, null, 2)}`);
            process.exit(1);
          }
          
          // Convert markdown to HTML with directive support
          const html = await convertMarkdownToHtml(content);
          
          // Create section slug from filename (remove .md extension)
          const slug = file.replace('.md', '');
          
          sections.push({
            id: frontmatter.id,
            slug,
            title: frontmatter.title,
            description: frontmatter.description,
            sidebar_position: frontmatter.sidebar_position,
            filePath,
            content,
            html
          });
          
        } catch (error) {
          console.error(`   ❌ Error processing ${file}:`, error);
        }
      }
      
      // Sort sections by sidebar_position
      sections.sort((a, b) => a.sidebar_position - b.sidebar_position);
      
      // Use learning path slug as the topic slug for direct files
      contentMap[learningPath].topics[learningPath] = {
        slug: learningPath,
        sections,
        metadata: learningPathMetadata ? {
          title: learningPathMetadata.title,
          order: learningPathMetadata.order,
          description: learningPathMetadata.description
        } : undefined
      };
      
      console.log(`   📄 ${learningPath} (direct files): ${sections.length} sections`);
    }
    
    console.log(`   📁 ${learningPath}: ${topics.length} topics`);
    
    for (const topic of topics) {
      const topicDir = path.join(learningPathDir, topic);
      const sections: Section[] = [];
      
      // Read topic metadata
      const metadata = readTopicMetadata(topicDir);
      
      // Get all markdown files (excluding quiz.md and _meta.json)
      const files = fs.readdirSync(topicDir).filter(file => 
        file.endsWith('.md') && file !== '_meta.json' && file !== 'quiz.md'
      );
      
      for (const file of files) {
        const filePath = path.join(topicDir, file);
        const fileContents = fs.readFileSync(filePath, 'utf8');
        
        try {
          const { data, content } = matter(fileContents);
          const frontmatter = data as FrontMatter;
          
          // Validate required fields
          if (!frontmatter.id || !frontmatter.title || !frontmatter.description || frontmatter.sidebar_position === undefined) {
            console.error(`   ❌ ERROR: ${file} in ${learningPath}/${topic} is missing required frontmatter fields`);
            console.error(`      Required: id, title, description, sidebar_position`);
            console.error(`      Found: ${JSON.stringify(frontmatter, null, 2)}`);
            process.exit(1);
          }
          
          // Convert markdown to HTML with directive support
          const html = await convertMarkdownToHtml(content);
          
          // Create section slug from filename (remove .md extension)
          const slug = file.replace('.md', '');
          
          sections.push({
            id: frontmatter.id,
            slug,
            title: frontmatter.title,
            description: frontmatter.description,
            sidebar_position: frontmatter.sidebar_position,
            filePath,
            content,
            html
          });
          
        } catch (error) {
          console.error(`   ❌ Error processing ${file}:`, error);
        }
      }
      
      // Sort sections by sidebar_position
      sections.sort((a, b) => a.sidebar_position - b.sidebar_position);
      
      contentMap[learningPath].topics[topic] = {
        slug: topic,
        sections,
        metadata
      };
      
      const displayTitle = metadata?.title || formatTitle(topic);
      console.log(`      ✓ ${displayTitle}: ${sections.length} sections`);
    }
  }
  
  console.log('\n✅ Content scan complete!\n');
  return contentMap;
}

// Step 2: Generate module structure JSON (ALL modules for global sidebar)
function generateModuleStructure(contentMap: ContentMap): void {
  console.log('📊 Generating module structure...');
  
  // Ensure data directory exists
  fs.mkdirSync(DATA_DIR, { recursive: true });
  
  // Create a GLOBAL module structure with ALL learning paths and topics
  const allModules: any[] = [];
  
  // Sort learning paths by metadata order, then alphabetically
  const sortedPaths = Object.entries(contentMap).sort(([pathA, dataA], [pathB, dataB]) => {
    const orderA = dataA.metadata?.order ?? Infinity;
    const orderB = dataB.metadata?.order ?? Infinity;
    
    if (orderA !== orderB) {
      return orderA - orderB;
    }
    
    // If orders are equal (or both undefined), sort alphabetically
    return pathA.localeCompare(pathB);
  });
  
  for (const [learningPath, learningPathData] of sortedPaths) {
    const topics = learningPathData.topics;
    
    // Convert topics object to array for sorting
    const topicsArray = Object.entries(topics).map(([slug, topic]) => ({
      slug,
      topic
    }));
    
    // Sort topics by metadata order, then alphabetically
    topicsArray.sort((a, b) => {
      const orderA = a.topic.metadata?.order ?? Infinity;
      const orderB = b.topic.metadata?.order ?? Infinity;
      
      if (orderA !== orderB) {
        return orderA - orderB;
      }
      
      // If orders are equal (or both missing), sort alphabetically
      return a.slug.localeCompare(b.slug);
    });
    
    // Create modules from sorted topics
    for (const { slug: topicSlug, topic } of topicsArray) {
      const displayTitle = topic.metadata?.title || formatTitle(topicSlug);
      
      const module = {
        id: `${learningPath}/${topicSlug}`,
        title: displayTitle,
        learningPath: getLearningPathTitle(learningPath),
        order: allModules.length + 1,
        pages: topic.sections.map((section, index) => {
          // Special handling for index.md in learning path root
          let slug: string;
          if (section.slug === 'index' && topicSlug === learningPath) {
            slug = `/learn/${learningPath}`;
          } else {
            slug = `/learn/${learningPath}/${topicSlug}/${section.slug}`;
          }
          
          return {
            id: section.id,
            title: section.title,
            slug,
            order: index + 1,
            completed: false
          };
        })
      };
      
      allModules.push(module);
    }
  }
  
  // Write to JSON file - single array of all modules
  const outputPath = path.join(DATA_DIR, 'modules.json');
  fs.writeFileSync(outputPath, JSON.stringify(allModules, null, 2));
  
  console.log(`✅ Module structure saved to ${outputPath}\n`);
}

function getLearningPathTitle(slug: string): string {
  const titles: { [key: string]: string} = {
    'devsecops': 'DevSecOps',
    'know_before_you_go': 'Know Before You Go',
    'cloud_security': 'Cloud Security',
    'cloud_security_development': 'Cloud Security Development',
    'application_security': 'Application Security'
  };
  return titles[slug] || formatTitle(slug);
}

// Helper function to format slug to title
function formatTitle(slug: string): string {
  return slug
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// Step 3: Generate TSX pages (one page per section)
function generatePages(contentMap: ContentMap): void {
  console.log('📝 Generating TSX pages...');
  
  let totalPages = 0;
  
  // Ensure public/quizzes directory exists
  const publicQuizzesDir = path.join(process.cwd(), 'public', 'quizzes');
  fs.mkdirSync(publicQuizzesDir, { recursive: true });
  
  // Ensure public/content directory exists for images
  const publicContentDir = path.join(process.cwd(), 'public', 'content');
  fs.mkdirSync(publicContentDir, { recursive: true });
  
  // Build a flat list of all topics with proper ordering
  const allTopics: Array<{ learningPath: string; topicSlug: string; topic: Topic }> = [];
  
  for (const [learningPath, learningPathData] of Object.entries(contentMap)) {
    const topics = learningPathData.topics;
    const topicsArray = Object.entries(topics).map(([slug, topic]) => ({
      learningPath,
      topicSlug: slug,
      topic
    }));
    
    // Sort by metadata order
    topicsArray.sort((a, b) => {
      const orderA = a.topic.metadata?.order ?? Infinity;
      const orderB = b.topic.metadata?.order ?? Infinity;
      
      if (orderA !== orderB) {
        return orderA - orderB;
      }
      
      return a.topicSlug.localeCompare(b.topicSlug);
    });
    
    allTopics.push(...topicsArray);
  }
  
  // Sort all topics globally by learning path order, then by topic order within each path
  allTopics.sort((a, b) => {
    // Get learning path metadata for ordering
    const pathOrderA = contentMap[a.learningPath].metadata?.order ?? Infinity;
    const pathOrderB = contentMap[b.learningPath].metadata?.order ?? Infinity;
    
    // First, sort by learning path order
    if (pathOrderA !== pathOrderB) {
      return pathOrderA - pathOrderB;
    }
    
    // Within the same learning path, sort by topic order
    const topicOrderA = a.topic.metadata?.order ?? Infinity;
    const topicOrderB = b.topic.metadata?.order ?? Infinity;
    
    if (topicOrderA !== topicOrderB) {
      return topicOrderA - topicOrderB;
    }
    
    // If everything is equal, sort alphabetically
    return a.topicSlug.localeCompare(b.topicSlug);
  });
  
  for (let topicIndex = 0; topicIndex < allTopics.length; topicIndex++) {
    const { learningPath, topicSlug, topic } = allTopics[topicIndex];
    const nextTopic = topicIndex < allTopics.length - 1 ? allTopics[topicIndex + 1] : null;
    
    // Check if quiz.md exists in the topic directory and copy it to public
    const topicDir = path.join(CONTENT_DIR, learningPath, topicSlug);
    const quizSourcePath = path.join(topicDir, 'quiz.md');
    
    if (fs.existsSync(quizSourcePath)) {
      const quizDestPath = path.join(publicQuizzesDir, `${topicSlug}-quiz.md`);
      fs.copyFileSync(quizSourcePath, quizDestPath);
      console.log(`   ✓ Copied quiz for ${topicSlug}`);
    }
    
    // Copy images directory if it exists
    const imagesSourceDir = path.join(topicDir, 'images');
    if (fs.existsSync(imagesSourceDir)) {
      const imagesDestDir = path.join(publicContentDir, learningPath, topicSlug, 'images');
      fs.mkdirSync(imagesDestDir, { recursive: true });
      
      // Copy all files from images directory
      const imageFiles = fs.readdirSync(imagesSourceDir);
      for (const imageFile of imageFiles) {
        const sourcePath = path.join(imagesSourceDir, imageFile);
        const destPath = path.join(imagesDestDir, imageFile);
        
        if (fs.statSync(sourcePath).isFile()) {
          fs.copyFileSync(sourcePath, destPath);
        }
      }
      console.log(`   ✓ Copied images for ${learningPath}/${topicSlug}`);
    }
    
    for (let i = 0; i < topic.sections.length; i++) {
      const section = topic.sections[i];
      const previousSection = i > 0 ? topic.sections[i - 1] : null;
      const nextSection = i < topic.sections.length - 1 ? topic.sections[i + 1] : null;
      
      // If this is the last section and there's a next topic, link to it
      const nextTopicFirstSection = (!nextSection && nextTopic) 
        ? nextTopic.topic.sections[0] 
        : null;
      
      // Special handling for index.md - create page at /learn/{learningPath}/ instead of /learn/{learningPath}/{topic}/index/
      let pageDir: string;
      if (section.slug === 'index' && topicSlug === learningPath) {
        // This is an index.md in the learning path root, create at /learn/{learningPath}/
        pageDir = path.join(APP_LEARN_DIR, learningPath);
      } else {
        // Normal case: /learn/{learningPath}/{topic}/{section}/
        pageDir = path.join(APP_LEARN_DIR, learningPath, topicSlug, section.slug);
      }
      
      fs.mkdirSync(pageDir, { recursive: true });
      
      // Generate page.tsx
      const pageContent = generatePageComponent(
        learningPath,
        topicSlug,
        section,
        previousSection,
        nextSection,
        nextTopicFirstSection,
        nextTopic,
        i + 1,
        topic.sections.length,
        topic.metadata
      );
      
      const pagePath = path.join(pageDir, 'page.tsx');
      fs.writeFileSync(pagePath, pageContent);
      
      totalPages++;
    }
  }
  
  console.log(`✅ Generated ${totalPages} pages!\n`);
}

// Generate page component
function generatePageComponent(
  learningPath: string,
  topicSlug: string,
  section: Section,
  previousSection: Section | null,
  nextSection: Section | null,
  nextTopicFirstSection: Section | null,
  nextTopic: { learningPath: string; topicSlug: string; topic: Topic } | null,
  currentPosition: number,
  totalSections: number,
  topicMetadata?: TopicMetadata
): string {
  const previousUrl = previousSection 
    ? `/learn/${learningPath}/${topicSlug}/${previousSection.slug}`
    : null;
  
  let nextUrl: string | null = null;
  if (nextSection) {
    nextUrl = `/learn/${learningPath}/${topicSlug}/${nextSection.slug}`;
  } else if (nextTopicFirstSection && nextTopic) {
    nextUrl = `/learn/${nextTopic.learningPath}/${nextTopic.topicSlug}/${nextTopicFirstSection.slug}`;
  }
  
  // Only show quiz on the last section of a topic (but not for welcome page)
  const isLastSection = currentPosition === totalSections;
  const isWelcomePage = learningPath === 'welcome';
  const quizPath = `/quizzes/${topicSlug}-quiz.md`;
  
  // Check if this is a capstone project
  const isCapstone = topicMetadata?.type === 'capstone';
  
  // Resolve relative image paths to absolute paths
  let processedHtml = section.html.replace(
    /(<img[^>]+src=")\.\/images\/([^"]+)(")/g,
    `$1/content/${learningPath}/${topicSlug}/images/$2$3`
  );
  
  // Escape the HTML content properly for template literal
  const escapedHtml = processedHtml
    .replace(/\\/g, '\\\\')
    .replace(/`/g, '\\`')
    .replace(/\$/g, '\\$');
  
  return `import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { PageNavigation } from '@/components/PageNavigation';
${isCapstone ? "import { CapstoneSubmissionForm } from '@/components/CapstoneSubmissionForm';" : "import { ModuleQuizWrapper } from '@/components/ModuleQuizWrapper';"}
import { WalkthroughLinkHydrator } from '@/components/WalkthroughLinkHydrator';
import { ExternalLinkHandler } from '@/components/ExternalLinkHandler';
import { CourseContentRenderer } from '@/components/CourseContentRenderer';

export default function Page() {
  return (
    <>
      <NavbarWithAuth
        showProgress={true}
        progressPercentage={${Math.round((currentPosition / totalSections) * 100)}}
        currentPath="${learningPath}"
      />
      
      <main className="min-h-screen pt-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            ${section.title}
          </h1>
          
          <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
            ${section.description}
          </p>
          
          <CourseContentRenderer html={\`${escapedHtml}\`} />
          
          {/* Handle external links */}
          <ExternalLinkHandler />
          
          {/* Hydrate walkthrough link placeholders */}
          <WalkthroughLinkHydrator />
          
          ${isCapstone 
            ? `{/* Capstone Submission Form */}
          <CapstoneSubmissionForm 
            contentId="${learningPath}-${topicSlug}"
          />`
            : (isLastSection && !isWelcomePage)
              ? `{/* Module Quiz - rendered after module content if quiz.md exists */}
          <ModuleQuizWrapper
            moduleId="${topicSlug}"
            quizPath="${quizPath}"
          />`
              : ''
          }
          
          <PageNavigation
            previousUrl={${previousUrl ? `"${previousUrl}"` : 'null'}}
            nextUrl={${nextUrl ? `"${nextUrl}"` : 'null'}}
            currentPosition={${currentPosition}}
            totalSections={${totalSections}}
          />
        </div>
      </main>
    </>
  );
}
`;
}

// Main execution
async function main() {
  try {
    const contentMap = await scanContentDirectory();
    generateModuleStructure(contentMap);
    generatePages(contentMap);
    
    console.log('🎉 All done! Pages generated successfully.\n');
    console.log('💡 Next steps:');
    console.log('   1. Run: npm run dev');
    console.log('   2. Visit: http://localhost:3001/learn/devsecops/what_is_application_security/introduction\n');
    
  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  }
}

main();
