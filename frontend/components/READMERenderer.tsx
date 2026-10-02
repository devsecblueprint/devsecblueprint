'use client';

import { useEffect, useState, useRef } from 'react';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkDirective from 'remark-directive';
import remarkGfm from 'remark-gfm';
import remarkRehype from 'remark-rehype';
import rehypeHighlight from 'rehype-highlight';
import rehypeStringify from 'rehype-stringify';
import { visit } from 'unist-util-visit';
import { ImageLightbox } from '@/components/ui/ImageLightbox';

interface READMERendererProps {
  markdown: string;
  walkthroughId: string;
}

// Escape text for safe embedding in an HTML attribute / text node.
function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// Remark plugin to extract ```mermaid fenced blocks into a placeholder div
// carrying the raw diagram source.
//
// The node is converted to a raw `html` node (not a transformed `code` node)
// because remark-rehype's default code handler always wraps code in a <pre>,
// which would both mis-style the diagram and trap the rendered SVG inside a
// preformatted block. Emitting a plain <div> keeps rehypeHighlight away from
// the definition and lets the client effect render it in place.
function remarkMermaid() {
  return (tree: any) => {
    visit(tree, 'code', (node: any) => {
      if (node.lang !== 'mermaid') {
        return;
      }

      // Preserve the raw definition both as a data attribute (used by the
      // render effect) and as text content (so it stays readable if rendering
      // ever fails). Browsers decode the entities back to the original source
      // when reading textContent / getAttribute.
      const escaped = escapeHtml(node.value);
      node.type = 'html';
      node.value = `<div class="mermaid-diagram" data-mermaid="${escaped}">${escaped}</div>`;
    });
  };
}

// Remark plugin to handle :::note directives
function remarkAdmonitions() {
  return (tree: any) => {
    visit(tree, (node) => {
      if (
        node.type === 'containerDirective' ||
        node.type === 'leafDirective'
      ) {
        const data = node.data || (node.data = {});
        const tagName = node.type === 'containerDirective' ? 'div' : 'div';

        data.hName = tagName;
        data.hProperties = {
          className: `admonition admonition-${node.name}`
        };

        // Add an empty title div - CSS ::before will add the text
        node.children = [
          {
            type: 'paragraph',
            data: {
              hName: 'div',
              hProperties: { className: 'admonition-title' }
            },
            children: [] // Empty - CSS will add the title via ::before
          },
          {
            type: 'paragraph',
            data: {
              hName: 'div',
              hProperties: { className: 'admonition-content' }
            },
            children: node.children
          }
        ];
      }
    });
  };
}

// Rehype plugin to ensure all images have alt text
function rehypeEnsureAltText() {
  return (tree: any) => {
    visit(tree, 'element', (node) => {
      if (node.tagName === 'img') {
        if (!node.properties.alt || node.properties.alt === '') {
          // Add default alt text if missing
          node.properties.alt = 'Image from walkthrough documentation';
        }
      }
    });
  };
}

// Rehype plugin to convert blockquotes to Docusaurus-style admonitions
function rehypeGitHubAlerts() {
  return (tree: any) => {
    visit(tree, 'element', (node) => {
      // Look for blockquotes that might be alerts or notes
      if (node.tagName === 'blockquote' && node.children && node.children.length > 0) {
        const firstChild = node.children[0];
        if (firstChild.type === 'element' && firstChild.tagName === 'p' && firstChild.children) {
          let alertType = null;
          let titleText = '';
          let contentModified = false;
          
          // Check for [!NOTE] style alerts
          const firstText = firstChild.children[0];
          if (firstText && firstText.type === 'text' && firstText.value) {
            const alertMatch = firstText.value.match(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]/);
            if (alertMatch) {
              alertType = alertMatch[1].toLowerCase();
              titleText = alertMatch[1].charAt(0).toUpperCase() + alertMatch[1].slice(1).toLowerCase();
              // Remove the alert marker from the text
              firstText.value = firstText.value.replace(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*/, '');
              contentModified = true;
            }
          }
          
          // Check for **Note:** style alerts (Docusaurus format)
          if (!alertType && firstChild.children.length >= 1) {
            const firstElement = firstChild.children[0];
            
            if (firstElement && firstElement.type === 'element' && firstElement.tagName === 'strong' && 
                firstElement.children && firstElement.children[0] && firstElement.children[0].type === 'text') {
              const strongText = firstElement.children[0].value;
              const match = strongText.match(/^(Note|Tip|Important|Warning|Caution):?$/i);
              
              if (match) {
                alertType = match[1].toLowerCase();
                // Capitalize first letter only
                titleText = match[1].charAt(0).toUpperCase() + match[1].slice(1).toLowerCase();
                
                // Remove the strong element completely
                firstChild.children.shift();
                
                // Clean up any leading colon/space in the next text node
                if (firstChild.children.length > 0 && firstChild.children[0].type === 'text') {
                  // Remove leading colon and whitespace
                  firstChild.children[0].value = firstChild.children[0].value.replace(/^:\s*/, '');
                  
                  // If the text node is now empty or just whitespace, remove it
                  if (!firstChild.children[0].value || !firstChild.children[0].value.trim()) {
                    firstChild.children.shift();
                  }
                }
                
                contentModified = true;
              }
            }
          }
          
          if (alertType && contentModified) {
            // Convert blockquote to div with Docusaurus-style structure
            node.tagName = 'div';
            
            // Store the original children before modifying
            const originalChildren = [...node.children];
            
            // Create title element (empty - CSS ::before will add the text)
            const titleElement = {
              type: 'element',
              tagName: 'div',
              properties: { className: 'admonition-title' },
              children: []
            };
            
            // Create content wrapper with the original children
            const contentElement = {
              type: 'element',
              tagName: 'div',
              properties: { className: 'admonition-content' },
              children: originalChildren
            };
            
            // Replace children with title + content structure
            node.children = [titleElement, contentElement];
            
            // Add Docusaurus-style classes
            node.properties = node.properties || {};
            node.properties.className = `admonition admonition-${alertType}`;
          }
        }
      }
    });
  };
}

export function READMERenderer({ markdown, walkthroughId }: READMERendererProps) {
  const [html, setHtml] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(true);
  const [lightboxImage, setLightboxImage] = useState<{ src: string; alt: string } | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function processMarkdown() {
      setIsProcessing(true);
      try {
        // Process markdown with remark/rehype pipeline
        const result = await unified()
          .use(remarkParse) // Parse markdown
          .use(remarkGfm) // Support GitHub Flavored Markdown
          .use(remarkDirective) // Support ::: directives
          .use(remarkAdmonitions) // Handle :::note directives
          .use(remarkMermaid) // Extract ```mermaid blocks before highlighting
          .use(remarkRehype, { allowDangerousHtml: true }) // Convert to HTML, allow raw HTML
          .use(rehypeEnsureAltText) // Ensure all images have alt text
          .use(rehypeGitHubAlerts) // Style GitHub alerts
          .use(rehypeHighlight) // Apply syntax highlighting
          .use(rehypeStringify, { allowDangerousHtml: true }) // Convert to string, preserve HTML
          .process(markdown);

        let processedHtml = String(result);

        // Resolve relative image paths
        // Replace relative image paths with absolute paths to the walkthrough directory
        processedHtml = processedHtml.replace(
          /(<img[^>]+src=")(?!http|\/|data:)([^"]+)(")/g,
          `$1/walkthroughs/${walkthroughId}/$2$3`
        );

        setHtml(processedHtml);
      } catch (error) {
        console.error('Error processing markdown:', error);
        setHtml('<p>Error rendering README content.</p>');
      } finally {
        setIsProcessing(false);
      }
    }

    processMarkdown();
  }, [markdown, walkthroughId]);

  // Render Mermaid diagrams after the HTML is mounted.
  // Mermaid is lazy-imported so the library only loads on pages that actually
  // contain diagrams, keeping it out of the bundle for everything else.
  useEffect(() => {
    if (!contentRef.current || isProcessing) return;

    const nodes = Array.from(
      contentRef.current.querySelectorAll<HTMLElement>('.mermaid-diagram')
    );
    if (nodes.length === 0) return;

    let cancelled = false;

    async function renderDiagrams(diagramNodes: HTMLElement[]) {
      try {
        const mermaid = (await import('mermaid')).default;

        const isDark = document.documentElement.classList.contains('dark');
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: 'strict',
          theme: isDark ? 'dark' : 'default',
        });

        for (let i = 0; i < diagramNodes.length; i++) {
          if (cancelled) return;

          const node = diagramNodes[i];
          const source = node.getAttribute('data-mermaid') ?? node.textContent ?? '';
          if (!source.trim()) continue;

          // Skip nodes already rendered (e.g. React re-run without remount)
          if (node.getAttribute('data-mermaid-rendered') === 'true') continue;

          const id = `mermaid-${walkthroughId}-${i}-${Date.now()}`;

          try {
            const { svg } = await mermaid.render(id, source);
            if (cancelled) return;
            node.innerHTML = svg;
            node.setAttribute('data-mermaid-rendered', 'true');
          } catch (renderError) {
            // Parsing/rendering failed: keep the raw definition readable
            // instead of showing a broken or empty diagram.
            console.error('Mermaid render failed:', renderError);
            const pre = document.createElement('pre');
            const code = document.createElement('code');
            code.textContent = source;
            pre.appendChild(code);
            node.innerHTML = '';
            node.appendChild(pre);
          }
        }
      } catch (importError) {
        console.error('Failed to load Mermaid:', importError);
      }
    }

    renderDiagrams(nodes);

    return () => {
      cancelled = true;
    };
  }, [html, isProcessing, walkthroughId]);

  // Add click handlers to images after HTML is rendered
  useEffect(() => {
    if (!contentRef.current || isProcessing) return;

    const images = contentRef.current.querySelectorAll('img');
    
    const handleImageClick = (e: Event) => {
      const img = e.target as HTMLImageElement;
      setLightboxImage({
        src: img.src,
        alt: img.alt || 'Image from documentation'
      });
    };

    images.forEach(img => {
      img.style.cursor = 'pointer';
      img.addEventListener('click', handleImageClick);
    });

    return () => {
      images.forEach(img => {
        img.removeEventListener('click', handleImageClick);
      });
    };
  }, [html, isProcessing]);

  if (isProcessing) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-gray-600 dark:text-gray-400">Loading README...</div>
      </div>
    );
  }

  return (
    <>
      <div
        ref={contentRef}
        className="prose prose-lg dark:prose-invert max-w-none
          prose-headings:font-bold prose-headings:text-gray-900 dark:prose-headings:text-gray-100
          prose-p:text-gray-700 dark:prose-p:text-gray-300
          prose-a:text-blue-600 dark:prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline
          prose-strong:text-gray-900 dark:prose-strong:text-gray-100
          prose-code:text-pink-600 dark:prose-code:text-pink-400 prose-code:bg-gray-100 dark:prose-code:bg-gray-800 prose-code:px-1 prose-code:py-0.5 prose-code:rounded
          prose-pre:bg-gray-900 dark:prose-pre:bg-gray-950 prose-pre:text-gray-100
          prose-blockquote:border-l-blue-600 dark:prose-blockquote:border-l-blue-400 prose-blockquote:text-gray-700 dark:prose-blockquote:text-gray-300
          prose-ul:text-gray-700 dark:prose-ul:text-gray-300
          prose-ol:text-gray-700 dark:prose-ol:text-gray-300
          prose-li:text-gray-700 dark:prose-li:text-gray-300
          prose-table:text-gray-700 dark:prose-table:text-gray-300
          prose-th:bg-gray-100 dark:prose-th:bg-gray-800
          prose-td:border-gray-300 dark:prose-td:border-gray-700
          prose-img:rounded-lg prose-img:shadow-md prose-img:mx-auto prose-img:cursor-pointer
          [&_.mermaid-diagram]:my-6 [&_.mermaid-diagram]:flex [&_.mermaid-diagram]:justify-center
          [&_.mermaid-diagram]:overflow-x-auto
          [&_.mermaid-diagram_svg]:max-w-full [&_.mermaid-diagram_svg]:h-auto"
        dangerouslySetInnerHTML={{ __html: html }}
      />
      
      <ImageLightbox
        src={lightboxImage?.src || ''}
        alt={lightboxImage?.alt || ''}
        isOpen={!!lightboxImage}
        onClose={() => setLightboxImage(null)}
      />
    </>
  );
}
