/**
 * Build-time Mermaid pre-rendering.
 *
 * The site is a static export deployed to CloudFront, so there is no server
 * runtime to render diagrams on demand, and rendering Mermaid in the browser
 * after mount proved fragile (imperative SVG injection into a
 * dangerouslySetInnerHTML container is wiped by React re-renders).
 *
 * Instead we render ```mermaid fenced blocks to SVG here, at build time, in a
 * JSDOM-backed Node environment. Each block becomes a self-contained markup
 * fragment carrying BOTH a light and a dark SVG; the client shows the correct
 * one via CSS based on the active theme. No Mermaid code ships to the browser.
 */

import { JSDOM } from 'jsdom';

// Matches a fenced ```mermaid code block and captures its body.
const MERMAID_BLOCK = /```mermaid[^\n]*\n([\s\S]*?)```/g;

type MermaidModule = {
  initialize: (config: Record<string, unknown>) => void;
  render: (id: string, src: string) => Promise<{ svg: string }>;
};

let mermaidPromise: Promise<MermaidModule> | null = null;

/**
 * Install the DOM globals and shims Mermaid 11 needs to render under Node,
 * then import the library once. Shims are required because JSDOM does not
 * implement SVG layout (getBBox / getComputedTextLength) or a constructable
 * CSSStyleSheet, both of which Mermaid uses during render.
 */
async function getMermaid(): Promise<MermaidModule> {
  if (mermaidPromise) {
    return mermaidPromise;
  }

  mermaidPromise = (async () => {
    const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
      pretendToBeVisual: true,
    });
    const { window } = dom;

    const g = globalThis as Record<string, unknown>;
    g.window = window;
    g.document = window.document;
    g.Element = window.Element;
    g.SVGElement = window.SVGElement;
    g.Node = window.Node;
    g.DOMParser = window.DOMParser;
    g.XMLSerializer = window.XMLSerializer;

    const svgProto = window.SVGElement.prototype as unknown as {
      getBBox?: () => { x: number; y: number; width: number; height: number };
      getComputedTextLength?: () => number;
    };
    if (!svgProto.getBBox) {
      svgProto.getBBox = () => ({ x: 0, y: 0, width: 100, height: 20 });
    }
    if (svgProto.getComputedTextLength === undefined) {
      svgProto.getComputedTextLength = () => 100;
    }

    // Mermaid references `CSSStyleSheet` as a bare global (resolved against
    // globalThis), and uses it as a constructable stylesheet. JSDOM only
    // exposes it on `window` and its implementation is not constructable the
    // way Mermaid needs, so we always install a working constructable version
    // on globalThis — either reusing window's if it constructs, or a shim.
    const tryConstruct = (C: unknown): boolean => {
      try {
        new (C as new () => unknown)();
        return true;
      } catch {
        return false;
      }
    };
    const winCss = (window as unknown as { CSSStyleSheet?: unknown }).CSSStyleSheet;
    if (winCss && tryConstruct(winCss)) {
      g.CSSStyleSheet = winCss;
    } else {
      class ShimCSSStyleSheet {
        cssRules: { cssText: string }[] = [];
        insertRule(rule: string, index = this.cssRules.length): number {
          this.cssRules.splice(index, 0, { cssText: rule });
          return index;
        }
        toString(): string {
          return this.cssRules.map((r) => r.cssText).join('\n');
        }
      }
      g.CSSStyleSheet = ShimCSSStyleSheet;
      (window as unknown as { CSSStyleSheet: unknown }).CSSStyleSheet =
        ShimCSSStyleSheet;
    }

    const mod = (await import('mermaid')) as unknown as { default: MermaidModule };
    return mod.default;
  })();

  return mermaidPromise;
}

/**
 * Render a single Mermaid definition to SVG for the given theme.
 * Returns null if rendering fails so the caller can fall back gracefully.
 */
async function renderOne(
  source: string,
  theme: 'default' | 'dark',
  id: string
): Promise<string | null> {
  try {
    const mermaid = await getMermaid();
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'strict',
      theme,
      // Deterministic output across builds (no random ids inside the SVG).
      deterministicIds: true,
      deterministicIDSeed: id,
    });
    const { svg } = await mermaid.render(id, source);
    return svg;
  } catch (error) {
    console.warn(`   ⚠️  Mermaid render failed (${theme}) for ${id}:`, error);
    return null;
  }
}

function escapeHtmlText(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

/**
 * Replace every ```mermaid block in `markdown` with pre-rendered SVG markup.
 *
 * Output per block:
 *   <div class="mermaid-diagram" data-mermaid-rendered="true">
 *     <div class="mermaid-light">…light SVG…</div>
 *     <div class="mermaid-dark">…dark SVG…</div>
 *   </div>
 *
 * If rendering fails for a block, the original fenced code is left intact so
 * the definition stays readable rather than vanishing.
 *
 * @param markdown  Raw README markdown.
 * @param slug      Walkthrough id, used to build stable diagram ids.
 * @returns         Markdown with mermaid blocks replaced by SVG markup.
 */
export async function prerenderMermaid(
  markdown: string,
  slug: string
): Promise<string> {
  // Collect blocks first (regex exec with global flag), then render async.
  const blocks: { match: string; source: string }[] = [];
  let m: RegExpExecArray | null;
  MERMAID_BLOCK.lastIndex = 0;
  while ((m = MERMAID_BLOCK.exec(markdown)) !== null) {
    blocks.push({ match: m[0], source: m[1].trimEnd() });
  }

  if (blocks.length === 0) {
    return markdown;
  }

  let result = markdown;
  for (let i = 0; i < blocks.length; i++) {
    const { match, source } = blocks[i];
    const baseId = `mmd-${slug}-${i}`;

    const [light, dark] = await Promise.all([
      renderOne(source, 'default', `${baseId}-light`),
      renderOne(source, 'dark', `${baseId}-dark`),
    ]);

    let replacement: string;
    if (light && dark) {
      replacement =
        `<div class="mermaid-diagram" data-mermaid-rendered="true">` +
        `<div class="mermaid-light">${light}</div>` +
        `<div class="mermaid-dark">${dark}</div>` +
        `</div>`;
    } else if (light || dark) {
      // Partial success: use whichever rendered for both slots.
      const svg = (light || dark) as string;
      replacement =
        `<div class="mermaid-diagram" data-mermaid-rendered="true">` +
        `<div class="mermaid-light">${svg}</div>` +
        `<div class="mermaid-dark">${svg}</div>` +
        `</div>`;
    } else {
      // Total failure: keep the raw definition visible and readable.
      replacement =
        `<pre class="mermaid-fallback"><code>${escapeHtmlText(source)}</code></pre>`;
    }

    // Replace only the first remaining occurrence of this exact block.
    result = result.replace(match, () => replacement);
  }

  return result;
}
