/**
 * Unit tests for LearningPageClient.
 */
import { render, waitFor } from '@testing-library/react';
import { useProgress } from '@/lib/hooks/useProgress';
import { useAllProgress } from '@/lib/hooks/useAllProgress';
import { LearningPageClient } from '@/components/LearningPageClient';
import type { Module } from '@/lib/types';

jest.mock('@/lib/hooks/useProgress', () => ({ useProgress: jest.fn() }));
jest.mock('@/lib/hooks/useAllProgress', () => ({ useAllProgress: jest.fn() }));
jest.mock('@/components/layout/Sidebar', () => ({
  Sidebar: ({ currentPageId }: { currentPageId: string }) => <div data-testid="sidebar">{currentPageId}</div>,
}));

const mockUseProgress = useProgress as jest.Mock;
const mockUseAllProgress = useAllProgress as jest.Mock;

const modules: Module[] = [
  {
    id: 'm1',
    title: 'M1',
    order: 1,
    pages: [{ id: 'p1', title: 'P1', slug: '/learn/devsecops/intro', order: 1, completed: false }],
  } as unknown as Module,
];

beforeEach(() => {
  jest.clearAllMocks();
  // @ts-expect-error cleanup
  delete (window as any).__markPageComplete;
});

it('renders the sidebar and exposes __markPageComplete globally', () => {
  mockUseProgress.mockReturnValue({ saveProgress: jest.fn() });
  mockUseAllProgress.mockReturnValue({ progress: {} });
  render(<LearningPageClient modules={modules} currentPageId="p1" contentPath="devsecops/intro" />);
  expect(typeof (window as any).__markPageComplete).toBe('function');
});

it('saves progress when markComplete is invoked for an incomplete page', async () => {
  const saveProgress = jest.fn().mockResolvedValue(undefined);
  mockUseProgress.mockReturnValue({ saveProgress });
  mockUseAllProgress.mockReturnValue({ progress: {} });
  render(<LearningPageClient modules={modules} currentPageId="p1" contentPath="devsecops/intro" />);
  await (window as any).__markPageComplete();
  expect(saveProgress).toHaveBeenCalledWith('devsecops/intro');
});

it('does not save progress for capstone pages', async () => {
  const saveProgress = jest.fn();
  mockUseProgress.mockReturnValue({ saveProgress });
  mockUseAllProgress.mockReturnValue({ progress: {} });
  render(<LearningPageClient modules={modules} currentPageId="p1" contentPath="devsecops/capstone" isCapstone />);
  await (window as any).__markPageComplete();
  expect(saveProgress).not.toHaveBeenCalled();
});

it('does not re-save an already-completed page', async () => {
  const saveProgress = jest.fn();
  mockUseProgress.mockReturnValue({ saveProgress });
  mockUseAllProgress.mockReturnValue({ progress: { 'devsecops/intro': true } });
  render(<LearningPageClient modules={modules} currentPageId="p1" contentPath="devsecops/intro" />);
  await (window as any).__markPageComplete();
  expect(saveProgress).not.toHaveBeenCalled();
});

it('cleans up the global on unmount', () => {
  mockUseProgress.mockReturnValue({ saveProgress: jest.fn() });
  mockUseAllProgress.mockReturnValue({ progress: {} });
  const { unmount } = render(<LearningPageClient modules={modules} currentPageId="p1" contentPath="devsecops/intro" />);
  expect((window as any).__markPageComplete).toBeDefined();
  unmount();
  expect((window as any).__markPageComplete).toBeUndefined();
});
