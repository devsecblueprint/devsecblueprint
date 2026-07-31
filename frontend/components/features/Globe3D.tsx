'use client';

import { useRef, useMemo, useEffect, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { COUNTRY_COORDINATES } from '@/lib/data/country-coordinates';

const GLOBE_RADIUS = 1.5;
const DOT_SIZE = 0.028;
const ROTATION_SPEED = 0.0015;

// Natural Earth 110m land boundaries — lightweight (~30KB), accurate enough for a globe
const GEOJSON_URL =
  'https://cdn.jsdelivr.net/npm/world-atlas@2/land-110m.json';

/**
 * Convert latitude/longitude to 3D position on a sphere.
 */
function latLonToVector3(lat: number, lon: number, radius: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);

  const x = -(radius * Math.sin(phi) * Math.cos(theta));
  const y = radius * Math.cos(phi);
  const z = radius * Math.sin(phi) * Math.sin(theta);

  return new THREE.Vector3(x, y, z);
}

// ─── GeoJSON Types ──────────────────────────────────────────────────────────

interface TopoJSON {
  type: string;
  objects: {
    land: {
      type: string;
      geometries: TopoGeometry[];
    };
  };
  arcs: number[][][];
  transform?: {
    scale: [number, number];
    translate: [number, number];
  };
}

interface TopoGeometry {
  type: string;
  arcs: number[] | number[][] | number[][][];
}

/**
 * Decode a TopoJSON arc index array into [lon, lat] coordinate pairs.
 */
function decodeArcs(topoJson: TopoJSON): [number, number][][] {
  const { arcs, transform } = topoJson;
  const scale = transform?.scale || [1, 1];
  const translate = transform?.translate || [0, 0];

  // Decode each arc (delta-encoded)
  const decodedArcs: [number, number][][] = arcs.map((arc) => {
    let x = 0;
    let y = 0;
    return arc.map(([dx, dy]) => {
      x += dx;
      y += dy;
      return [x * scale[0] + translate[0], y * scale[1] + translate[1]] as [number, number];
    });
  });

  return decodedArcs;
}

/**
 * Extract polylines from TopoJSON land object.
 */
function extractLandLines(topoJson: TopoJSON): [number, number][][] {
  const decodedArcs = decodeArcs(topoJson);
  const lines: [number, number][][] = [];

  const geometries = topoJson.objects.land.geometries;

  for (const geom of geometries) {
    if (geom.type === 'Polygon') {
      const rings = geom.arcs as number[][];
      for (const ring of rings) {
        const line = resolveRing(ring, decodedArcs);
        if (line.length > 1) lines.push(line);
      }
    } else if (geom.type === 'MultiPolygon') {
      const polygons = geom.arcs as number[][][];
      for (const polygon of polygons) {
        for (const ring of polygon) {
          const line = resolveRing(ring, decodedArcs);
          if (line.length > 1) lines.push(line);
        }
      }
    }
  }

  return lines;
}

/**
 * Resolve a ring of arc indices into coordinates.
 */
function resolveRing(
  ring: number[],
  decodedArcs: [number, number][][]
): [number, number][] {
  const coords: [number, number][] = [];

  for (const arcIndex of ring) {
    const reverse = arcIndex < 0;
    const idx = reverse ? ~arcIndex : arcIndex;
    const arc = decodedArcs[idx];
    if (!arc) continue;

    const points = reverse ? [...arc].reverse() : arc;

    for (let i = coords.length === 0 ? 0 : 1; i < points.length; i++) {
      coords.push(points[i]);
    }
  }

  return coords;
}

// ─── Globe Components ───────────────────────────────────────────────────────

/**
 * Hook to fetch and parse land boundaries.
 */
function useLandLines() {
  const [lines, setLines] = useState<[number, number][][]>([]);

  useEffect(() => {
    let cancelled = false;

    fetch(GEOJSON_URL)
      .then((res) => res.json())
      .then((topoJson: TopoJSON) => {
        if (cancelled) return;
        const extracted = extractLandLines(topoJson);
        setLines(extracted);
      })
      .catch(() => {
        // Silently fail — globe renders without outlines
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return lines;
}

/**
 * Renders continent/country outlines as gold lines on the sphere.
 */
function LandOutlines({ lines }: { lines: [number, number][][] }) {
  const lineObjects = useMemo(() => {
    const material = new THREE.LineBasicMaterial({
      color: '#ffbe00',
      transparent: true,
      opacity: 0.6,
    });

    return lines.map((line) => {
      // Subsample long lines to keep vertex count reasonable
      const step = line.length > 200 ? 3 : line.length > 100 ? 2 : 1;
      const points: THREE.Vector3[] = [];

      for (let i = 0; i < line.length; i += step) {
        const [lon, lat] = line[i];
        points.push(latLonToVector3(lat, lon, GLOBE_RADIUS + 0.004));
      }
      // Always include last point
      if (line.length > 0) {
        const [lon, lat] = line[line.length - 1];
        const last = latLonToVector3(lat, lon, GLOBE_RADIUS + 0.004);
        if (points.length === 0 || !points[points.length - 1].equals(last)) {
          points.push(last);
        }
      }

      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      return new THREE.Line(geometry, material);
    });
  }, [lines]);

  return (
    <>
      {lineObjects.map((obj, index) => (
        <primitive key={`land-${index}`} object={obj} />
      ))}
    </>
  );
}

/**
 * The rotating globe mesh with land outlines, wireframe sphere, and country dots.
 */
function GlobeMesh() {
  const groupRef = useRef<THREE.Group>(null);
  const landLines = useLandLines();

  // Auto-rotate
  useFrame(() => {
    if (groupRef.current) {
      groupRef.current.rotation.y += ROTATION_SPEED;
    }
  });

  // Pre-compute dot positions
  const dotPositions = useMemo(() => {
    return COUNTRY_COORDINATES.map((country) =>
      latLonToVector3(country.lat, country.lon, GLOBE_RADIUS + 0.012)
    );
  }, []);

  const dotGeometry = useMemo(() => new THREE.SphereGeometry(DOT_SIZE, 8, 8), []);
  const dotMaterial = useMemo(
    () =>
      new THREE.MeshBasicMaterial({
        color: '#ffbe00',
        transparent: true,
        opacity: 1,
      }),
    []
  );

  return (
    <group ref={groupRef} rotation={[0.2, -0.5, 0.05]}>
      {/* Globe sphere — dark base */}
      <mesh>
        <sphereGeometry args={[GLOBE_RADIUS, 64, 64]} />
        <meshBasicMaterial color="#0a0a1a" transparent opacity={0.95} />
      </mesh>

      {/* Faint latitude/longitude grid */}
      <mesh>
        <sphereGeometry args={[GLOBE_RADIUS + 0.001, 36, 18]} />
        <meshBasicMaterial color="#1a1a3a" wireframe transparent opacity={0.15} />
      </mesh>

      {/* Land outlines in gold */}
      {landLines.length > 0 && <LandOutlines lines={landLines} />}

      {/* Country dots */}
      {dotPositions.map((position, index) => (
        <mesh
          key={index}
          geometry={dotGeometry}
          material={dotMaterial}
          position={position}
        />
      ))}

      {/* Connecting arcs */}
      <ArcLines />
    </group>
  );
}

/**
 * Subtle arc lines connecting major hub regions.
 */
function ArcLines() {
  const arcObjects = useMemo(() => {
    const material = new THREE.LineBasicMaterial({
      color: '#ffbe00',
      transparent: true,
      opacity: 0.25,
    });

    const connections: [number, number, number, number][] = [
      [37.09, -95.71, 51.17, 10.45],   // US → Germany
      [37.09, -95.71, 35.86, 104.20],   // US → China
      [51.17, 10.45, 20.59, 78.96],     // Germany → India
      [1.35, 103.82, 35.86, 104.20],    // Singapore → China
      [9.08, 8.68, 55.38, -3.44],       // Nigeria → UK
      [-14.24, -51.93, 37.09, -95.71],  // Brazil → US
    ];

    return connections.map(([lat1, lon1, lat2, lon2]) => {
      const start = latLonToVector3(lat1, lon1, GLOBE_RADIUS + 0.015);
      const end = latLonToVector3(lat2, lon2, GLOBE_RADIUS + 0.015);

      const mid = new THREE.Vector3()
        .addVectors(start, end)
        .multiplyScalar(0.5)
        .normalize()
        .multiplyScalar(GLOBE_RADIUS + 0.35);

      const curve = new THREE.QuadraticBezierCurve3(start, mid, end);
      const points = curve.getPoints(48);
      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      return new THREE.Line(geometry, material);
    });
  }, []);

  return (
    <>
      {arcObjects.map((obj, index) => (
        <primitive key={`arc-${index}`} object={obj} />
      ))}
    </>
  );
}

/**
 * Globe3D component — renders the 3D rotating globe with country data.
 * Respects reduced-motion preference.
 */
export function Globe3D() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mql.matches);
    const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, []);

  return (
    <div
      className="w-full aspect-square max-w-[320px] sm:max-w-[360px] mx-auto"
      aria-hidden="true"
    >
      <Canvas
        camera={{ position: [0, 0, 4], fov: 45 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        <ambientLight intensity={0.4} />
        <pointLight position={[10, 10, 10]} intensity={0.2} />
        {!prefersReducedMotion && <GlobeMesh />}
        {prefersReducedMotion && <StaticGlobeMesh />}
        <OrbitControls
          enableZoom={false}
          enablePan={false}
          autoRotate={false}
          rotateSpeed={0.4}
        />
      </Canvas>
    </div>
  );
}

/**
 * Static version of the globe for reduced-motion preference.
 */
function StaticGlobeMesh() {
  const landLines = useLandLines();

  const dotPositions = useMemo(() => {
    return COUNTRY_COORDINATES.map((country) =>
      latLonToVector3(country.lat, country.lon, GLOBE_RADIUS + 0.012)
    );
  }, []);

  const dotGeometry = useMemo(() => new THREE.SphereGeometry(DOT_SIZE, 8, 8), []);
  const dotMaterial = useMemo(
    () =>
      new THREE.MeshBasicMaterial({
        color: '#ffbe00',
        transparent: true,
        opacity: 1,
      }),
    []
  );

  return (
    <group rotation={[0.2, -0.5, 0.05]}>
      <mesh>
        <sphereGeometry args={[GLOBE_RADIUS, 64, 64]} />
        <meshBasicMaterial color="#0a0a1a" transparent opacity={0.95} />
      </mesh>
      <mesh>
        <sphereGeometry args={[GLOBE_RADIUS + 0.001, 36, 18]} />
        <meshBasicMaterial color="#1a1a3a" wireframe transparent opacity={0.15} />
      </mesh>
      {landLines.length > 0 && <LandOutlines lines={landLines} />}
      {dotPositions.map((position, index) => (
        <mesh key={index} geometry={dotGeometry} material={dotMaterial} position={position} />
      ))}
    </group>
  );
}
