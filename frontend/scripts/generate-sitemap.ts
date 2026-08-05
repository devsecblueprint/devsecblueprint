/**
 * Generate sitemap.xml for public (non-authenticated) pages.
 *
 * Run during build to produce public/sitemap.xml so that Google and other
 * search engines can discover and index all publicly accessible content.
 */

import * as fs from 'fs';
import * as path from 'path';

const SITE_URL = 'https://devsecblueprint.com';

// Public routes that should be indexed by search engines.
// These are pages that do NOT require authentication (no AuthGuard).
const PUBLIC_ROUTES: Array<{ path: string; changefreq: string; priority: number }> = [
  { path: '/', changefreq: 'weekly', priority: 1.0 },
  { path: '/about', changefreq: 'monthly', priority: 0.8 },
  { path: '/about/contact', changefreq: 'monthly', priority: 0.6 },
  { path: '/about/faq', changefreq: 'monthly', priority: 0.6 },
  { path: '/about/leadership', changefreq: 'monthly', priority: 0.6 },
  { path: '/courses', changefreq: 'weekly', priority: 0.9 },
  { path: '/curriculum', changefreq: 'weekly', priority: 0.9 },
  { path: '/faq', changefreq: 'monthly', priority: 0.6 },
  { path: '/login', changefreq: 'yearly', priority: 0.3 },
  { path: '/pricing', changefreq: 'monthly', priority: 0.8 },
  { path: '/sponsorships', changefreq: 'monthly', priority: 0.5 },
];

function generateSitemap(): string {
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD

  const urls = PUBLIC_ROUTES.map(
    (route) => `  <url>
    <loc>${SITE_URL}${route.path}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>${route.changefreq}</changefreq>
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
console.log(`✓ Sitemap generated at ${outputPath} (${PUBLIC_ROUTES.length} URLs)`);
