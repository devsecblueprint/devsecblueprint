import React from 'react';
import { render, waitFor, fireEvent } from '@testing-library/react';

import { READMERenderer } from '@/components/READMERenderer';

// Mermaid diagrams are pre-rendered to light+dark SVG at build time and
// embedded into the README markdown as raw HTML. These tests feed the
// component that same markup and verify the renderer surfaces both theme
// variants and wires click-to-zoom via the lightbox. No client-side mermaid
// is involved anymore.

const LIGHT_SVG =
  '<svg xmlns="http://www.w3.org/2000/svg" id="light-svg" width="100" height="50"><rect width="100" height="50" fill="#fff"/></svg>';
const DARK_SVG =
  '<svg xmlns="http://www.w3.org/2000/svg" id="dark-svg" width="100" height="50"><rect width="100" height="50" fill="#000"/></svg>';

// Markdown containing a pre-rendered mermaid block, exactly as the build-time
// prerenderMermaid step emits it.
const MARKDOWN = [
  '# Heading',
  '',
  `<div class="mermaid-diagram" data-mermaid-rendered="true"><div class="mermaid-light">${LIGHT_SVG}</div><div class="mermaid-dark">${DARK_SVG}</div></div>`,
  '',
  'Trailing text.',
].join('\n');

describe('READMERenderer pre-rendered Mermaid', () => {
  afterEach(() => {
    document.documentElement.classList.remove('dark');
  });

  it('renders both the light and dark pre-rendered SVG variants', async () => {
    const { container } = render(
      <READMERenderer markdown={MARKDOWN} walkthroughId="test-wt" />
    );

    await waitFor(() => {
      expect(
        container.querySelector('.mermaid-diagram[data-mermaid-rendered="true"]')
      ).toBeInTheDocument();
    });

    const light = container.querySelector('.mermaid-light svg');
    const dark = container.querySelector('.mermaid-dark svg');
    expect(light).toBeInTheDocument();
    expect(dark).toBeInTheDocument();
  });

  it('does not wrap the diagram in a <pre> code block', async () => {
    const { container } = render(
      <READMERenderer markdown={MARKDOWN} walkthroughId="test-wt" />
    );

    await waitFor(() => {
      expect(container.querySelector('.mermaid-diagram')).toBeInTheDocument();
    });

    expect(container.querySelector('.mermaid-diagram')!.closest('pre')).toBeNull();
  });

  it('makes the diagram an accessible button (role + tabindex)', async () => {
    const { container } = render(
      <READMERenderer markdown={MARKDOWN} walkthroughId="test-wt" />
    );

    await waitFor(() => {
      const d = container.querySelector('.mermaid-diagram') as HTMLElement;
      expect(d).toBeInTheDocument();
      expect(d.getAttribute('role')).toBe('button');
      expect(d.getAttribute('tabindex')).toBe('0');
    });
  });

  it('opens the lightbox with the light SVG when clicked in light mode', async () => {
    const { container } = render(
      <READMERenderer markdown={MARKDOWN} walkthroughId="test-wt" />
    );

    await waitFor(() => {
      const d = container.querySelector('.mermaid-diagram') as HTMLElement;
      expect(d.getAttribute('role')).toBe('button');
    });

    fireEvent.click(container.querySelector('.mermaid-diagram') as HTMLElement);

    await waitFor(() => {
      const img = document.querySelector(
        'img[src^="data:image/svg+xml"]'
      ) as HTMLImageElement | null;
      expect(img).toBeInTheDocument();
      // The light variant should be the one serialized into the lightbox.
      expect(decodeURIComponent(img!.src)).toContain('id="light-svg"');
    });
  });

  it('opens the lightbox with the dark SVG when clicked in dark mode', async () => {
    document.documentElement.classList.add('dark');

    const { container } = render(
      <READMERenderer markdown={MARKDOWN} walkthroughId="test-wt" />
    );

    await waitFor(() => {
      const d = container.querySelector('.mermaid-diagram') as HTMLElement;
      expect(d.getAttribute('role')).toBe('button');
    });

    fireEvent.click(container.querySelector('.mermaid-diagram') as HTMLElement);

    await waitFor(() => {
      const img = document.querySelector(
        'img[src^="data:image/svg+xml"]'
      ) as HTMLImageElement | null;
      expect(img).toBeInTheDocument();
      expect(decodeURIComponent(img!.src)).toContain('id="dark-svg"');
    });
  });

  it('opens the lightbox on keyboard Enter', async () => {
    const { container } = render(
      <READMERenderer markdown={MARKDOWN} walkthroughId="test-wt" />
    );

    await waitFor(() => {
      const d = container.querySelector('.mermaid-diagram') as HTMLElement;
      expect(d.getAttribute('role')).toBe('button');
    });

    fireEvent.keyDown(container.querySelector('.mermaid-diagram') as HTMLElement, {
      key: 'Enter',
    });

    await waitFor(() => {
      expect(
        document.querySelector('img[src^="data:image/svg+xml"]')
      ).toBeInTheDocument();
    });
  });
});
