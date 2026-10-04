/**
 * Unit tests for Globe3D.
 *
 * The react-three-fiber Canvas and drei controls are mocked so the component's
 * own logic (geometry math, land-line parsing, reduced-motion branch) runs in
 * jsdom without a real WebGL context.
 */
import { render, waitFor } from '@testing-library/react';
import { Globe3D } from '@/components/features/Globe3D';

// Canvas renders its children directly; useFrame is a no-op.
jest.mock('@react-three/fiber', () => ({
  Canvas: ({ children }: { children: React.ReactNode }) => <div data-testid="canvas">{children}</div>,
  useFrame: jest.fn(),
}));
jest.mock('@react-three/drei', () => ({ OrbitControls: () => null }));

// A minimal valid TopoJSON land payload so extractLandLines runs.
const TOPO = {
  type: 'Topology',
  transform: { scale: [1, 1], translate: [0, 0] },
  arcs: [
    [[0, 0], [10, 0], [0, 10], [-10, 0], [0, -10]],
  ],
  objects: {
    land: {
      type: 'GeometryCollection',
      geometries: [{ type: 'Polygon', arcs: [[0]] }],
    },
  },
};

const mockFetch = jest.fn();
global.fetch = mockFetch;

function setMatchMedia(matches: boolean) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation((query: string) => ({
      matches,
      media: query,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
}

beforeEach(() => {
  jest.clearAllMocks();
  mockFetch.mockResolvedValue({ json: () => Promise.resolve(TOPO) });
});

it('renders the animated globe canvas (motion allowed)', async () => {
  setMatchMedia(false);
  const { getByTestId } = render(<Globe3D />);
  expect(getByTestId('canvas')).toBeInTheDocument();
  // Land data fetch kicks off from the mounted mesh
  await waitFor(() => expect(mockFetch).toHaveBeenCalled());
});

it('renders the static globe when reduced motion is preferred', async () => {
  setMatchMedia(true);
  const { getByTestId } = render(<Globe3D />);
  expect(getByTestId('canvas')).toBeInTheDocument();
  await waitFor(() => expect(mockFetch).toHaveBeenCalled());
});

it('still renders when the land-data fetch fails', async () => {
  setMatchMedia(false);
  mockFetch.mockRejectedValue(new Error('offline'));
  const { getByTestId } = render(<Globe3D />);
  expect(getByTestId('canvas')).toBeInTheDocument();
  await waitFor(() => expect(mockFetch).toHaveBeenCalled());
});
