/**
 * Unit tests for the Sidebar — exported nav-state helpers and component behavior.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import {
  Sidebar,
  computeDefaultNavState,
  readNavState,
  writeNavState,
  applyAutoExpand,
} from '@/components/layout/Sidebar';
import type { Module } from '@/lib/types';

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));

function mod(id: string, pageIds: string[], extra: Record<string, unknown> = {}): Module {
  return {
    id,
    title: `Module ${id}`,
    order: 1,
    pages: pageIds.map((pid) => ({ id: pid, title: pid, slug: `/learn/${pid}`, order: 1, completed: false })),
    ...extra,
  } as unknown as Module;
}

beforeEach(() => localStorage.clear());

describe('computeDefaultNavState', () => {
  it('expands only the module containing the current page', () => {
    const modules = [mod('m1', ['p1', 'p2']), mod('m2', ['p3'])];
    const state = computeDefaultNavState(modules, 'p3');
    expect(state).toEqual({ m1: false, m2: true });
  });

  it('collapses everything when the current page is unknown', () => {
    const modules = [mod('m1', ['p1'])];
    expect(computeDefaultNavState(modules, 'nope')).toEqual({ m1: false });
  });
});

describe('readNavState / writeNavState', () => {
  it('round-trips a valid state', () => {
    writeNavState({ m1: true, m2: false });
    expect(readNavState()).toEqual({ m1: true, m2: false });
  });

  it('returns null when no state is stored', () => {
    expect(readNavState()).toBeNull();
  });

  it('clears and returns null on corrupted JSON', () => {
    localStorage.setItem('sidebar-nav-state', '{not json');
    expect(readNavState()).toBeNull();
    expect(localStorage.getItem('sidebar-nav-state')).toBeNull();
  });

  it('rejects a non-object (array) payload', () => {
    localStorage.setItem('sidebar-nav-state', '[1,2,3]');
    expect(readNavState()).toBeNull();
  });
});

describe('applyAutoExpand', () => {
  const modules = [mod('m1', ['p1']), mod('m2', ['p2'])];

  it('expands the module with the current page', () => {
    const result = applyAutoExpand({ m1: false, m2: false }, modules, 'p2');
    expect(result.m2).toBe(true);
  });

  it('returns state unchanged when no current page', () => {
    const state = { m1: false, m2: false };
    expect(applyAutoExpand(state, modules, undefined)).toBe(state);
  });

  it('returns state unchanged when the module is already expanded', () => {
    const state = { m1: false, m2: true };
    expect(applyAutoExpand(state, modules, 'p2')).toBe(state);
  });

  it('returns state unchanged when the page is not found', () => {
    const state = { m1: false, m2: false };
    expect(applyAutoExpand(state, modules, 'ghost')).toBe(state);
  });
});

describe('Sidebar component', () => {
  it('renders module titles', () => {
    const modules = [mod('m1', ['p1'], { learningPath: 'DevSecOps' })];
    render(<Sidebar modules={modules} currentPageId="p1" />);
    expect(screen.getAllByText('Module m1').length).toBeGreaterThan(0);
  });

  it('persists collapsed state to localStorage via the width toggle effect', () => {
    const modules = [mod('m1', ['p1'], { learningPath: 'DevSecOps' })];
    render(<Sidebar modules={modules} currentPageId="p1" />);
    // The collapsed-state effect writes the key on mount.
    expect(localStorage.getItem('sidebar-collapsed')).toBe('false');
  });
});
