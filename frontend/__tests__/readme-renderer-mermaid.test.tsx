import React from 'react';
import { render, waitFor } from '@testing-library/react';

import { READMERenderer } from '@/components/READMERenderer';

// Mermaid diagrams render client-side (a real browser provides correct text
// metrics / layout). Here we mock the mermaid library so `render()` returns a
// deterministic SVG and verify the component turns a ```mermaid block into a
// .mermaid-diagram div and injects the rendered SVG. (Click-to-zoom removed.)

const mockRender = jest.fn(async (id: string, _source: string) => ({
  svg: `<svg id="${id}" xmlns="http://www.w3.org/2000/svg" width="200" height="120"><rect width="200" height="120"/></svg>`,
}));
const mockInitialize = jest.fn();

jest.mock('mermaid', () => ({
  __esModule: true,
  default: {
    initialize: (...args: unknown[]) => mockInitialize(...args),
    render: (...args: [string, string]) => mockRender(...args),
  },
}));

const MARKDOWN = [
  '# Heading',
  '',
  '```mermaid',
  'flowchart LR',
  '    A[Start] --> B[End]',
  '```',
  '',
  'Trailing text.',
].join('\n');

describe('READMERenderer client-side Mermaid', () => {
  beforeEach(() => {
    mockRender.mockClear();
    mockInitialize.mockClear();
  });

  it('renders the mermaid block as a diagram div, not a <pre> code block', async () => {
    const { container } = render(
      <READMERenderer markdown={MARKDOWN} walkthroughId="test-wt" />
    );

    await waitFor(() => {
      expect(container.querySelector('.mermaid-diagram')).toBeInTheDocument();
    });

    expect(container.querySelector('.mermaid-diagram')!.closest('pre')).toBeNull();
  });

  it('renders the diagram SVG into the diagram div', async () => {
    const { container } = render(
      <READMERenderer markdown={MARKDOWN} walkthroughId="test-wt" />
    );

    await waitFor(() => {
      const d = container.querySelector(
        '.mermaid-diagram[data-mermaid-rendered="true"]'
      );
      expect(d).toBeInTheDocument();
      expect(d!.querySelector('svg')).toBeInTheDocument();
    });

    expect(mockRender).toHaveBeenCalledTimes(1);
  });

  it('passes the diagram source to mermaid.render', async () => {
    render(<READMERenderer markdown={MARKDOWN} walkthroughId="test-wt" />);

    await waitFor(() => {
      expect(mockRender).toHaveBeenCalled();
    });

    const [, source] = mockRender.mock.calls[0];
    expect(source).toContain('flowchart LR');
    expect(source).toContain('A[Start] --> B[End]');
  });
});
