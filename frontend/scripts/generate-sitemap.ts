/**
 * Generate sitemap.xml for public (non-authenticated) pages.
 *
 * Run during build to produce public/sitemap.xml so that Google and other
 * search engines can discover and index all publicly accessible content.
 *
 * Includes dynamically generated walkthrough and module preview routes.
 */

import * as fs from 'fs';
import * as path from 'path';

const SITE_URL = 'https://devsecblueprint.com';

// --- Load walkthrough IDs dynamically from content/walkthroughs/*/metadata.json ---
const walkthroughsContentDir = path.join(process.cwd(), 'content', 'walkthroughs');
const walkthroughIds: string[] = fs.readdirSync(walkthroughsContentDir, { withFileTypes: true })
  .filter((d) => d.isDirectory() && !d.name.startsWith('.'))
  .map((d) => {
    const metaPath = path.join(walkthroughsContentDir, d.name, 'metadata.json');
    if (!fs.existsSync(metaPath)) return null;
    const meta = JSON.parse(fs.readFileSync(metaPath, 'utf-8'));
    return meta.id as string;
  })
  .filter((id): id is string => id !== null);

// --- Load module slugs and learning path slugs from modules.json ---
interface ModuleJson {
  id: string;
  title: string;
  learningPath: string;
  pages: unknown[];
}
const modulesJsonPath = path.join(process.cwd(), 'lib', 'data', 'modules.json');
const modulesData: ModuleJson[] = JSON.parse(fs.readFileSync(modulesJsonPath, 'utf-8'));
const moduleSlugs: string[] = modulesData.map((m) => m.id.replace(/\//g, '--'));

// Derive unique learning path slugs
function slugify(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}
const learningPathSlugs: string[] = [
  ...new Set(modulesData.map((m) => slugify(m.learningPath))),
];

// --- Static public routes ---
const PUBLIC_ROUTES: Array<{ path: string; priority: number }> = [
  { path: '/', priority: 1.0 },
  { path: '/about', priority: 0.8 },
  { path: '/about/contact', priority: 0.6 },
  { path: '/about/faq', priority: 0.6 },
  { path: '/about/leadership', priority: 0.6 },
  { path: '/courses', priority: 0.9 },
  { path: '/curriculum', priority: 0.9 },
  { path: '/faq', priority: 0.6 },
  { path: '/login', priority: 0.3 },
  { path: '/pricing', priority: 0.8 },
  { path: '/sponsorships', priority: 0.5 },
];

// --- Dynamic preview routes ---
const walkthroughPreviewRoutes = [
  // Walkthrough listing page
  { path: '/walkthroughs/preview', priority: 0.8 },
  // Individual walkthrough previews
  ...walkthroughIds.map((id) => ({
    path: `/walkthroughs/preview/${id}`,
    priority: 0.7,
  })),
];

const videoPreviewRoutes = [
  // Video preview listing page
  { path: '/videos/preview', priority: 0.8 },
];

const modulePreviewRoutes = moduleSlugs.map((slug) => ({
  path: `/courses/preview/${slug}`,
  priority: 0.7,
}));

const learningPathPreviewRoutes = learningPathSlugs.map((slug) => ({
  path: `/courses/preview/path/${slug}`,
  priority: 0.8,
}));

const ALL_ROUTES = [...PUBLIC_ROUTES, ...walkthroughPreviewRoutes, ...videoPreviewRoutes, ...learningPathPreviewRoutes, ...modulePreviewRoutes];

function generateSitemap(): string {
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD

  const urls = ALL_ROUTES.map(
    (route) => `  <url>
    <loc>${SITE_URL}${route.path}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>${route.priority.toFixed(1)}</priority>
  </url>`
  ).join('\n');

  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>
`;
}

// Write sitemap to public/ so it's included in the static export
const outputPath = path.join(process.cwd(), 'public', 'sitemap.xml');
fs.writeFileSync(outputPath, generateSitemap(), 'utf-8');
console.log(`✓ Sitemap generated at ${outputPath} (${ALL_ROUTES.length} URLs)`);
