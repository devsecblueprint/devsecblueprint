/**
 * Unit tests for BuilderJourneyWidget.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { useBuilderJourney } from '@/lib/hooks/useBuilderJourney';
import { FREE_JOURNEY_PHASES } from '@/lib/data/builder-journey';
import { BuilderJourneyWidget } from '@/components/dashboard/BuilderJourneyWidget';

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));
jest.mock('@/lib/hooks/useBuilderJourney', () => ({ useBuilderJourney: jest.fn() }));
const mockHook = useBuilderJourney as jest.Mock;

function state(overrides: Record<string, unknown> = {}) {
  return {
    taskStatuses: {},
    currentPhase: 1,
    completionPercentage: 20,
    recommendedAction: null,
    recentCompletions: [],
    isComplete: false,
    isLoading: false,
    error: null,
    notEligible: false,
    tier: 'FREE',
    completeTask: jest.fn(),
    ...overrides,
  };
}

beforeEach(() => jest.clearAllMocks());

it('renders nothing when the user is not eligible', () => {
  mockHook.mockReturnValue(state({ notEligible: true }));
  const { container } = render(<BuilderJourneyWidget />);
  expect(container).toBeEmptyDOMElement();
});

it('renders nothing when the journey is complete', () => {
  mockHook.mockReturnValue(state({ isComplete: true }));
  const { container } = render(<BuilderJourneyWidget />);
  expect(container).toBeEmptyDOMElement();
});

it('shows a loading skeleton', () => {
  mockHook.mockReturnValue(state({ isLoading: true }));
  const { container } = render(<BuilderJourneyWidget />);
  expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
});

it('shows an error state with retry', () => {
  mockHook.mockReturnValue(state({ error: 'boom' }));
  render(<BuilderJourneyWidget />);
  expect(screen.getByText(/Unable to load your journey progress/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
});

it('renders phase + progress and a recommended action', () => {
  mockHook.mockReturnValue(
    state({
      currentPhase: 1,
      completionPercentage: 40,
      recommendedAction: { title: 'Join Discord', description: 'Connect', actionUrl: 'https://discord.gg/x' },
    }),
  );
  render(<BuilderJourneyWidget />);
  expect(screen.getByText(`Phase 1 of ${FREE_JOURNEY_PHASES.length}`)).toBeInTheDocument();
  expect(screen.getByText('40%')).toBeInTheDocument();
  expect(screen.getByText('Join Discord')).toBeInTheDocument();
});

it('expands the current phase task list', () => {
  mockHook.mockReturnValue(state({ currentPhase: FREE_JOURNEY_PHASES[0].phase }));
  render(<BuilderJourneyWidget />);
  const toggle = screen.getByRole('button', { name: /view phase .* tasks/i });
  fireEvent.click(toggle);
  // First task title from the phase should now appear
  const firstTask = FREE_JOURNEY_PHASES[0].tasks[0];
  expect(screen.getAllByText(firstTask.title).length).toBeGreaterThan(0);
});

it('shows recent completions', () => {
  mockHook.mockReturnValue(
    state({ recentCompletions: [{ taskId: 't1', title: 'Completed Task', status: 'completed' }] }),
  );
  render(<BuilderJourneyWidget />);
  expect(screen.getByText('Completed Task')).toBeInTheDocument();
});
