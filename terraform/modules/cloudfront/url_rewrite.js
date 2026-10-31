import cf from 'cloudfront';

const kvs = cf.kvs();

var SITE_NAME = 'The DevSec Blueprint';
var DEFAULT_OG_IMAGE = 'https://devsecblueprint.com/og-image.png';
var CRAWLER_PATTERN = /Discordbot|Twitterbot|Slackbot|LinkedInBot|facebookexternalhit|WhatsApp|TelegramBot/i;

async function handler(event) {
    var request = event.request;
    var host = request.headers.host.value;
    
    // Redirect www to apex domain
    if (host.startsWith('www.')) {
        var apexDomain = host.substring(4);
        return {
            statusCode: 301,
            statusDescription: 'Moved Permanently',
            headers: {
                'location': { value: 'https://' + apexDomain + request.uri }
            }
        };
    }
    
    var uri = request.uri;
    
    // Legacy Docusaurus route redirects (301 Moved Permanently)
    // Localized routes
    if (uri.match(/^\/(zh-CN|fr|es|de|ja|ko|pt-BR|ru)\//)) {
        var stripped = uri.replace(/^\/(zh-CN|fr|es|de|ja|ko|pt-BR|ru)/, '');
        var dest = stripped || '/';
        // Map known legacy paths to current equivalents
        dest = mapLegacyPath(dest);
        return {
            statusCode: 301,
            statusDescription: 'Moved Permanently',
            headers: {
                'location': { value: 'https://' + host + dest }
            }
        };
    }
    
    // Non-localized legacy path redirects
    var legacyDest = mapLegacyPath(uri);
    if (legacyDest !== uri) {
        return {
            statusCode: 301,
            statusDescription: 'Moved Permanently',
            headers: {
                'location': { value: 'https://' + host + legacyDest }
            }
        };
    }
    
    // Check if URI already has an extension
    if (!uri.includes('.')) {
        // Rewrite dynamic video detail routes to the catch-all page
        // Exclude /videos/preview which is a real static page
        if (uri.match(/^\/videos\/[^\/]+$/) && uri !== '/videos/_' && uri !== '/videos/preview') {
            request.uri = '/videos/_.html';
            return request;
        }
        // Rewrite video preview routes
        if (uri.match(/^\/videos\/preview\/[^\/]+$/) && uri !== '/videos/preview/_') {
            // Link-preview crawlers get a synthetic OG page built from the Key Value Store
            var uaHeader = request.headers['user-agent'];
            if (isCrawler(uaHeader && uaHeader.value)) {
                var html = await tryBuildPreview(uri, host);
                if (html) {
                    return {
                        statusCode: 200,
                        statusDescription: 'OK',
                        headers: {
                            'content-type': { value: 'text/html; charset=utf-8' },
                            'cache-control': { value: 'public, max-age=300' }
                        },
                        body: html
                    };
                }
            }
            request.uri = '/videos/preview/_.html';
            return request;
        }
        // Check if URI ends with /
        if (uri.endsWith('/')) {
            request.uri = uri + 'index.html';
        } else {
            request.uri = uri + '.html';
        }
    }
    
    return request;
}

function mapLegacyPath(path) {
    // Legacy Docusaurus curriculum/learning pages -> /curriculum
    if (path.match(/^\/(docs|prerequisites|projects\/)/)) {
        return '/curriculum';
    }
    // Legacy category pages
    if (path.match(/^\/category\//)) {
        return '/curriculum';
    }
    // Legacy blog/news pages
    if (path.match(/^\/blog/)) {
        return '/';
    }
    // Legacy pricing/membership
    if (path.match(/^\/(membership|plans|subscribe)/)) {
        return '/pricing';
    }
    // Legacy about/team pages (exact paths only, not /team/* assets)
    if (path.match(/^\/(team|contributors)\/?$/)) {
        return '/about/leadership';
    }
    // Legacy search page
    if (path.match(/^\/search/)) {
        return '/';
    }
    // Legacy Docusaurus tags
    if (path.match(/^\/tags/)) {
        return '/curriculum';
    }
    return path;
}

function isCrawler(ua) {
    return typeof ua === 'string' && CRAWLER_PATTERN.test(ua);
}

function escapeHtml(value) {
    return String(value === undefined || value === null ? '' : value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function buildHtml(meta, slug, host) {
    var title = (meta && meta.t) || SITE_NAME;
    var description = (meta && meta.d) || '';
    var image = meta && typeof meta.i === 'string' && /^https:\/\//i.test(meta.i) ? meta.i : DEFAULT_OG_IMAGE;
    var pageUrl = 'https://' + (host || 'devsecblueprint.com') + '/videos/preview/' + encodeURIComponent(slug);

    var t = escapeHtml(title);
    var d = escapeHtml(description);
    var i = escapeHtml(image);
    var u = escapeHtml(pageUrl);

    return '<!DOCTYPE html>\n' +
        '<html lang="en">\n' +
        '<head>\n' +
        '<meta charset="utf-8">\n' +
        '<title>' + t + '</title>\n' +
        '<meta name="description" content="' + d + '">\n' +
        '<meta property="og:title" content="' + t + '">\n' +
        '<meta property="og:description" content="' + d + '">\n' +
        '<meta property="og:image" content="' + i + '">\n' +
        '<meta property="og:url" content="' + u + '">\n' +
        '<meta property="og:type" content="video.other">\n' +
        '<meta property="og:site_name" content="' + escapeHtml(SITE_NAME) + '">\n' +
        '<meta name="twitter:card" content="summary_large_image">\n' +
        '<meta name="twitter:title" content="' + t + '">\n' +
        '<meta name="twitter:description" content="' + d + '">\n' +
        '<meta name="twitter:image" content="' + i + '">\n' +
        '</head>\n' +
        '<body>\n' +
        '<p><a href="' + u + '">' + t + '</a></p>\n' +
        '</body>\n' +
        '</html>\n';
}

// Returns an HTML string for the slug in uri, or null on any miss/error
async function tryBuildPreview(uri, host) {
    try {
        var slug = uri.substring('/videos/preview/'.length);
        try {
            slug = decodeURIComponent(slug);
        } catch (e) {
            return null;
        }
        var raw = await kvs.get(slug);
        var meta = JSON.parse(raw);
        if (!meta || typeof meta !== 'object') {
            return null;
        }
        return buildHtml(meta, slug, host);
    } catch (e) {
        return null;
    }
}
