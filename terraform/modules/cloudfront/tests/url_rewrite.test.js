'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const SOURCE = fs.readFileSync(path.join(__dirname, '..', 'url_rewrite.js'), 'utf8');

// Load the CloudFront function source with `import cf from 'cloudfront'` stubbed out.
function load(store) {
  const stubbed = SOURCE.replace(
    /^import cf from 'cloudfront';\s*$/m,
    ''
  );
  assert.notStrictEqual(stubbed, SOURCE, 'import line should be present and stripped');
  const cf = {
    kvs: () => ({
      get: async (key) => {
        if (!Object.prototype.hasOwnProperty.call(store, key)) {
          throw new Error('KeyNotFound');
        }
        return store[key];
      },
    }),
  };
  const factory = new Function(
    'cf',
    stubbed + '\nreturn { handler, isCrawler, escapeHtml, buildHtml };'
  );
  return factory(cf);
}

function req(uri, ua, host = 'devsecblueprint.com') {
  const headers = { host: { value: host } };
  if (ua !== undefined) headers['user-agent'] = { value: ua };
  return { request: { uri, headers } };
}

const BROWSER_UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36';
const DISCORD_UA = 'Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)';
const DEFAULT_IMAGE = 'https://devsecblueprint.com/og-image.png';

test('source stays under the 10 KB CloudFront Functions limit', () => {
  assert.ok(Buffer.byteLength(SOURCE) < 10 * 1024);
});

test('crawler UA + known slug returns synthetic 200 HTML with OG tags', async () => {
  const fn = load({
    'my-video': JSON.stringify({ t: 'My Video', d: 'A description', i: 'https://img.example.com/t.png' }),
  });
  const res = await fn.handler(req('/videos/preview/my-video', DISCORD_UA));
  assert.strictEqual(res.statusCode, 200);
  assert.strictEqual(res.statusDescription, 'OK');
  assert.strictEqual(res.headers['content-type'].value, 'text/html; charset=utf-8');
  assert.strictEqual(res.headers['cache-control'].value, 'public, max-age=300');
  assert.match(res.body, /<title>My Video<\/title>/);
  assert.match(res.body, /<meta property="og:title" content="My Video">/);
  assert.match(res.body, /<meta property="og:description" content="A description">/);
  assert.match(res.body, /<meta property="og:image" content="https:\/\/img\.example\.com\/t\.png">/);
  assert.match(res.body, /<meta property="og:url" content="https:\/\/devsecblueprint\.com\/videos\/preview\/my-video">/);
  assert.match(res.body, /<meta property="og:type" content="video\.other">/);
  assert.match(res.body, /<meta property="og:site_name" content="The DevSec Blueprint">/);
  assert.match(res.body, /<meta name="twitter:card" content="summary_large_image">/);
  assert.match(res.body, /<meta name="twitter:title" content="My Video">/);
  assert.match(res.body, /<meta name="twitter:description" content="A description">/);
  assert.match(res.body, /<meta name="twitter:image" content="https:\/\/img\.example\.com\/t\.png">/);
});

test('every listed crawler UA is recognised, case-insensitively', () => {
  const fn = load({});
  for (const ua of ['Discordbot', 'Twitterbot', 'Slackbot', 'LinkedInBot', 'facebookexternalhit', 'WhatsApp', 'TelegramBot']) {
    assert.ok(fn.isCrawler(`x ${ua}/1.0`), ua);
    assert.ok(fn.isCrawler(ua.toLowerCase()), ua.toLowerCase());
  }
  assert.ok(!fn.isCrawler(BROWSER_UA));
  assert.ok(!fn.isCrawler(undefined));
  assert.ok(!fn.isCrawler(''));
});

test('crawler UA + unknown slug (kvs throws) falls through to preview rewrite', async () => {
  const fn = load({});
  const res = await fn.handler(req('/videos/preview/nope', DISCORD_UA));
  assert.strictEqual(res.uri, '/videos/preview/_.html');
});

test('crawler UA + invalid JSON in kvs falls through', async () => {
  const fn = load({ bad: 'not json' });
  const res = await fn.handler(req('/videos/preview/bad', DISCORD_UA));
  assert.strictEqual(res.uri, '/videos/preview/_.html');
});

test('crawler UA + malformed percent-encoding falls through', async () => {
  const fn = load({});
  const res = await fn.handler(req('/videos/preview/%E0%A4%A', DISCORD_UA));
  assert.strictEqual(res.uri, '/videos/preview/_.html');
});

test('browser UA falls through even when slug is in the store', async () => {
  const fn = load({ 'my-video': JSON.stringify({ t: 'T', d: 'D', i: '' }) });
  const res = await fn.handler(req('/videos/preview/my-video', BROWSER_UA));
  assert.strictEqual(res.uri, '/videos/preview/_.html');
});

test('missing user-agent header falls through', async () => {
  const fn = load({ 'my-video': JSON.stringify({ t: 'T', d: 'D', i: '' }) });
  const res = await fn.handler(req('/videos/preview/my-video'));
  assert.strictEqual(res.uri, '/videos/preview/_.html');
});

test('title, description and image are HTML-escaped', async () => {
  const fn = load({
    x: JSON.stringify({ t: `A "quoted" <b>&</b> 'title'`, d: '<script>alert(1)</script>', i: 'https://e.com/a.png?x=1&y="2"' }),
  });
  const res = await fn.handler(req('/videos/preview/x', DISCORD_UA));
  assert.ok(res.body.includes('content="A &quot;quoted&quot; &lt;b&gt;&amp;&lt;/b&gt; &#39;title&#39;"'));
  assert.ok(!res.body.includes('<script>'));
  assert.ok(!res.body.includes('<b>'));
  assert.ok(res.body.includes('content="&lt;script&gt;alert(1)&lt;/script&gt;"'));
  assert.ok(res.body.includes('https://e.com/a.png?x=1&amp;y=&quot;2&quot;'));
});

test('escapeHtml escapes all five characters', () => {
  const fn = load({});
  assert.strictEqual(fn.escapeHtml(`&<>"'`), '&amp;&lt;&gt;&quot;&#39;');
  assert.strictEqual(fn.escapeHtml(undefined), '');
});

test('missing or non-https thumbnail falls back to default image', async () => {
  const fn = load({
    a: JSON.stringify({ t: 'A', d: 'D', i: '' }),
    b: JSON.stringify({ t: 'B', d: 'D' }),
    c: JSON.stringify({ t: 'C', d: 'D', i: 'http://insecure.example.com/x.png' }),
    d: JSON.stringify({ t: 'D', d: 'D', i: 'javascript:alert(1)' }),
  });
  for (const slug of ['a', 'b', 'c', 'd']) {
    const res = await fn.handler(req(`/videos/preview/${slug}`, DISCORD_UA));
    assert.ok(res.body.includes(`<meta property="og:image" content="${DEFAULT_IMAGE}">`), slug);
    assert.ok(res.body.includes(`<meta name="twitter:image" content="${DEFAULT_IMAGE}">`), slug);
  }
});

test('buildHtml produces a valid-looking document with a link to the page', () => {
  const fn = load({});
  const html = fn.buildHtml({ t: 'T', d: 'D', i: '' }, 'slug-1', 'devsecblueprint.com');
  assert.ok(html.startsWith('<!DOCTYPE html>'));
  assert.ok(html.includes('<a href="https://devsecblueprint.com/videos/preview/slug-1">'));
  assert.ok(html.trim().endsWith('</html>'));
});

test('existing: www redirects to apex', async () => {
  const fn = load({});
  const res = await fn.handler(req('/about', BROWSER_UA, 'www.devsecblueprint.com'));
  assert.strictEqual(res.statusCode, 301);
  assert.strictEqual(res.headers.location.value, 'https://devsecblueprint.com/about');
});

test('existing: legacy redirects', async () => {
  const fn = load({});
  let res = await fn.handler(req('/docs/foo', BROWSER_UA));
  assert.strictEqual(res.statusCode, 301);
  assert.strictEqual(res.headers.location.value, 'https://devsecblueprint.com/curriculum');
  res = await fn.handler(req('/fr/blog', BROWSER_UA));
  assert.strictEqual(res.headers.location.value, 'https://devsecblueprint.com/');
});

test('existing: /videos/foo -> /videos/_.html', async () => {
  const fn = load({});
  assert.strictEqual((await fn.handler(req('/videos/foo', BROWSER_UA))).uri, '/videos/_.html');
});

test('existing: /videos/preview and /videos/preview/_ are not video detail routes', async () => {
  const fn = load({});
  assert.strictEqual((await fn.handler(req('/videos/preview', BROWSER_UA))).uri, '/videos/preview.html');
  assert.strictEqual((await fn.handler(req('/videos/preview/_', DISCORD_UA))).uri, '/videos/preview/_.html');
});

test('existing: /about -> /about.html, / -> /index.html, trailing slash, extensions untouched', async () => {
  const fn = load({});
  assert.strictEqual((await fn.handler(req('/about', BROWSER_UA))).uri, '/about.html');
  assert.strictEqual((await fn.handler(req('/', BROWSER_UA))).uri, '/index.html');
  assert.strictEqual((await fn.handler(req('/about/', BROWSER_UA))).uri, '/about/index.html');
  assert.strictEqual((await fn.handler(req('/_next/app.js', BROWSER_UA))).uri, '/_next/app.js');
});

test('crawler on non-preview routes is unaffected', async () => {
  const fn = load({ about: JSON.stringify({ t: 'x' }) });
  assert.strictEqual((await fn.handler(req('/about', DISCORD_UA))).uri, '/about.html');
});
