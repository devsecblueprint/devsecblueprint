'use client';

import { useState } from 'react';
import { BroadcastComposer } from './BroadcastComposer';
import { BroadcastHistory } from './BroadcastHistory';

/**
 * Thin wrapper composing the broadcast composer and history.
 * A successful send bumps the refresh key so History reloads.
 */
export function BroadcastManagement() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">
        Broadcast Notifications
      </h2>
      <div className="mb-8">
        <BroadcastComposer onSent={() => setRefreshKey((k) => k + 1)} />
      </div>
      <BroadcastHistory refreshKey={refreshKey} />
    </div>
  );
}
