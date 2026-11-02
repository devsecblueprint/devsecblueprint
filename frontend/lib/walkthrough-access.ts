/**
 * Walkthrough access tier helpers.
 *
 * A walkthrough with an explicit tier record uses it; any walkthrough missing
 * from the map falls back to the default tier. A failed tier request fails
 * closed (everything is treated as BUILDER).
 */

import type { ApiResponse } from '@/lib/api';

export type WalkthroughTier = 'FREE' | 'BUILDER';

export interface WalkthroughTierMap {
  tiers: Record<string, string>;
  defaultTier: WalkthroughTier;
}

interface AccessTiersPayload {
  access_tiers?: Record<string, string> | null;
  default_tier?: string;
}

/** Map used before/without a successful tier response: fail closed. */
export const FAIL_CLOSED_TIER_MAP: WalkthroughTierMap = { tiers: {}, defaultTier: 'BUILDER' };

export function resolveWalkthroughTiers(
  response: Pick<ApiResponse<AccessTiersPayload>, 'data' | 'error' | 'statusCode'> | null | undefined
): WalkthroughTierMap {
  if (!response || response.error || !response.data) {
    return { tiers: {}, defaultTier: 'BUILDER' };
  }

  const { access_tiers, default_tier } = response.data;
  const tiers =
    access_tiers && typeof access_tiers === 'object' && !Array.isArray(access_tiers) ? access_tiers : {};

  // An older backend omits default_tier and only listed locked walkthroughs,
  // so unlisted ones were free. Keep that meaning during a rolling deploy.
  // A present but unrecognized value fails closed.
  const defaultTier: WalkthroughTier =
    default_tier === undefined || default_tier === null || default_tier === 'FREE' ? 'FREE' : 'BUILDER';

  return { tiers, defaultTier };
}

export function getWalkthroughTier(id: string, map: WalkthroughTierMap): WalkthroughTier {
  const explicit = Object.prototype.hasOwnProperty.call(map.tiers, id) ? map.tiers[id] : undefined;
  return explicit === 'FREE' || explicit === 'BUILDER' ? explicit : map.defaultTier;
}

export function isWalkthroughLocked(id: string, map: WalkthroughTierMap): boolean {
  return getWalkthroughTier(id, map) === 'BUILDER';
}
