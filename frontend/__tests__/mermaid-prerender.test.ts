/**
 * @jest-environment node
 */

// Validates the block-detection / replacement / fallback logic of the
// build-time Mermaid pre-renderer. The actual Mermaid library (ESM) is mocked
// here so Jest's CJS transform does not have to parse it; the real end-to-end
// render (jsdom + Mermaid) is exercised during the build via tsx. The mock
// returns a theme-tagged stub SVG so we can assert both variants are emitted.
jest.mock('mermaid', () => ({
  __esModule: true,
  default: {
    initialize: jest.fn(),
    render: jest.fn(async (id: string) => ({
      svg: `<svg xmlns="http://www.w3.org/2000/svg" id="${id}"><rect/></svg>`,
    })),
  },
}));

import { prerenderMermaid } from '@/scripts/lib/mermaid-prerender';

describe('prerenderMermaid', () => {
  it('leaves markdown without mermaid blocks unchanged', async () => {
    const md = '# Title\n\nSome text with a `code` span.\n';
    const out = await prerenderMermaid(md, 'wt');
    expect(out).toBe(md);
  });

  it('replaces a mermaid block with light + dark pre-rendered SVG markup', async () => {
    const md = [
      '# Title',
      '',
      '```mermaid',
      'flowchart LR',
      '  A[Start] --> B[End]',
      '```',
      '',
      'After.',
    ].join('\n');

    const out = await prerenderMermaid(md, 'wt');

    // No raw fenced mermaid should remain.
    expect(out).not.toContain('```mermaid');
    // Diagram wrapper + both theme variants present.
    expect(out).toContain('class="mermaid-diagram"');
    expect(out).toContain('data-mermaid-rendered="true"');
    expect(out).toContain('class="mermaid-light"');
    expect(out).toContain('class="mermaid-dark"');
    // Two real SVG elements (light + dark), not escaped text.
    expect(out.split('<svg').length - 1).toBe(2);
    expect(out).not.toContain('&lt;svg');
    // Surrounding markdown preserved.
    expect(out).toContain('# Title');
    expect(out).toContain('After.');
  });

  it('handles multiple mermaid blocks', async () => {
    const md = [
      '```mermaid',
      'flowchart LR',
      '  A --> B',
      '```',
      '',
      'between',
      '',
      '```mermaid',
      'flowchart TB',
      '  C --> D',
      '```',
    ].join('\n');

    const out = await prerenderMermaid(md, 'wt');

    expect(out.split('class="mermaid-diagram"').length - 1).toBe(2);
    expect(out.split('<svg').length - 1).toBe(4); // 2 blocks x light+dark
    expect(out).toContain('between');
  });

  it('falls back to a readable code block when both themes fail to render', async () => {
    // Force the mocked renderer to throw for this case.
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const mermaid = require('mermaid').default as { render: jest.Mock };
    mermaid.render.mockRejectedValueOnce(new Error('parse error'));
    mermaid.render.mockRejectedValueOnce(new Error('parse error'));

    const md = ['```mermaid', 'this is not valid mermaid !!!', '```'].join('\n');

    const out = await prerenderMermaid(md, 'wt-fail');

    // On failure we keep the definition readable rather than dropping it.
    expect(out).toContain('mermaid-fallback');
    expect(out).toContain('this is not valid mermaid');
    expect(out).not.toContain('```mermaid');
  });
});
