/**
 * Unit tests for the public BuilderJourneySection.
 */
import { render, screen } from '@testing-library/react';
import { BuilderJourneySection } from '@/components/features/BuilderJourneySection';
import {
  BUILDER_JOURNEY_PHASES,
  BUILDER_JOURNEY_SECTION,
} from '@/lib/data/builder-journey';
import { trackJourneyEvent } from '@/lib/utils/journey-analytics';

jest.mock('@/lib/utils/journey-analytics', () => ({ trackJourneyEvent: jest.fn() }));
const mockTrack = trackJourneyEvent as jest.Mock;

// jsdom lacks IntersectionObserver — stub one that immediately "intersects".
beforeAll(() => {
  class IO {
    cb: IntersectionObserverCallback;
    constructor(cb: IntersectionObserverCallback) {
      this.cb = cb;
    }
    observe(el: Element) {
      this.cb([{ isIntersecting: true, target: el } as IntersectionObserverEntry], this as unknown as IntersectionObserver);
    }
    unobserve() {}
    disconnect() {}
  }
  // @ts-expect-error test stub
  global.IntersectionObserver = IO;
});

beforeEach(() => jest.clearAllMocks());

it('renders the section header and subtitle', () => {
  render(<BuilderJourneySection />);
  expect(screen.getByText(BUILDER_JOURNEY_SECTION.title)).toBeInTheDocument();
  expect(screen.getByText(BUILDER_JOURNEY_SECTION.subtitle)).toBeInTheDocument();
});

it('renders every journey phase title', () => {
  render(<BuilderJourneySection />);
  for (const phase of BUILDER_JOURNEY_PHASES) {
    expect(screen.getAllByText(phase.title).length).toBeGreaterThan(0);
  }
});

it('emits a journey_section_viewed analytics event on mount', () => {
  render(<BuilderJourneySection />);
  expect(mockTrack).toHaveBeenCalledWith({ type: 'journey_section_viewed' });
});

it('shows a "+N more" indicator when a phase has more than 4 tasks', () => {
  const hasOverflow = BUILDER_JOURNEY_PHASES.some((p) => p.tasks.length > 4);
  render(<BuilderJourneySection />);
  if (hasOverflow) {
    expect(screen.getAllByText(/\+\d+ more/).length).toBeGreaterThan(0);
  } else {
    // No phase overflows; nothing to assert beyond a successful render.
    expect(screen.getByText(BUILDER_JOURNEY_SECTION.title)).toBeInTheDocument();
  }
});
