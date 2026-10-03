/**
 * Unit tests for the ModuleList navigation component.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { ModuleList } from '@/components/features/ModuleList';
import type { Module } from '@/lib/types';

function mod(id: string, pages: Array<{ id: string; completed: boolean }>): Module {
  return {
    id,
    title: `Module ${id}`,
    order: 1,
    pages: pages.map((p) => ({ id: p.id, title: `Page ${p.id}`, slug: `page-${p.id}`, order: 1, completed: p.completed })),
  } as unknown as Module;
}

it('renders modules with page completion counts', () => {
  render(<ModuleList modules={[mod('m1', [{ id: 'p1', completed: true }, { id: 'p2', completed: false }])]} />);
  expect(screen.getByText('Module m1')).toBeInTheDocument();
  expect(screen.getByText('1/2')).toBeInTheDocument();
  // Pages expanded by default
  expect(screen.getByText('Page p1')).toBeInTheDocument();
});

it('collapses and expands a module', () => {
  render(<ModuleList modules={[mod('m1', [{ id: 'p1', completed: false }])]} />);
  const header = screen.getByRole('button', { name: /Module m1/i });
  expect(header).toHaveAttribute('aria-expanded', 'true');
  fireEvent.click(header);
  expect(header).toHaveAttribute('aria-expanded', 'false');
  expect(screen.queryByText('Page p1')).not.toBeInTheDocument();
});

it('marks the current page with aria-current', () => {
  render(
    <ModuleList
      modules={[mod('m1', [{ id: 'p1', completed: false }, { id: 'p2', completed: false }])]}
      currentPageId="p2"
    />,
  );
  const current = screen.getByText('Page p2').closest('a');
  expect(current).toHaveAttribute('aria-current', 'page');
});

it('invokes onPageClick and prevents default navigation', () => {
  const onPageClick = jest.fn();
  render(
    <ModuleList modules={[mod('m1', [{ id: 'p1', completed: false }])]} onPageClick={onPageClick} />,
  );
  fireEvent.click(screen.getByText('Page p1'));
  expect(onPageClick).toHaveBeenCalledWith('p1');
});

it('shows a filled completion icon when all pages are done', () => {
  const { container } = render(
    <ModuleList modules={[mod('m1', [{ id: 'p1', completed: true }, { id: 'p2', completed: true }])]} />,
  );
  expect(screen.getByText('2/2')).toBeInTheDocument();
  // Completed pages render an SVG with aria-label "Completed"
  expect(container.querySelectorAll('[aria-label="Completed"]').length).toBe(2);
});
