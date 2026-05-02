/**
 * Mock MarkdownRenderer for Jest tests.
 * The real component uses ESM-only dependencies (unified, remark, rehype)
 * that require extensive transform configuration. This mock provides
 * the same interface for testing components that import MarkdownRenderer.
 */
export default function MarkdownRenderer({ markdown }: { markdown: string }) {
  return <div data-testid="markdown-renderer">{markdown}</div>;
}
