/**
 * Playback Progress Hooks
 *
 * Provides progress tracking and playback token management for
 * the recording player. Implements debounced progress saving
 * (15-30s interval) with pause and seek triggers.
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  fetchProgress,
  requestPlaybackToken,
  saveProgress,
} from '@/lib/video-client';
import type { ProgressResponse } from '@/lib/video-types';

/**
 * Playback progress hook return type.
 */
interface UsePlaybackProgressReturn {
  progress: ProgressResponse | null;
  isLoading: boolean;
  error: string | null;
  saveCurrentProgress: (
    positionSeconds: number,
    durationSeconds: number
  ) => void;
  isSaving: boolean;
}

/**
 * Playback token hook return type.
 */
interface UsePlaybackTokenReturn {
  token: string | null;
  expiresInSeconds: number | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

const SAVE_INTERVAL_MS = 20000; // 20 seconds
const SEEK_THRESHOLD_S = 5; // 5 seconds

/**
 * Hook to manage playback progress for a recording.
 *
 * Implements:
 * - Initial progress fetch on mount
 * - Debounced auto-save every 15-30 seconds during playback
 * - Immediate save on pause and significant seek events
 *
 * @param recordingId - The recording identifier.
 * @returns Progress state and save function.
 */
export function usePlaybackProgress(
  recordingId: string
): UsePlaybackProgressReturn {
  const [progress, setProgress] = useState<ProgressResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const lastSavedPositionRef = useRef<number>(0);
  const lastSaveTimeRef = useRef<number>(0);
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Fetch initial progress
  useEffect(() => {
    if (!recordingId) return;

    const loadProgress = async () => {
      setIsLoading(true);
      const { data, error: apiError } = await fetchProgress(recordingId);
      if (data) {
        setProgress(data);
        lastSavedPositionRef.current = data.positionSeconds ?? 0;
      } else {
        setError(apiError || 'Failed to load progress');
      }
      setIsLoading(false);
    };

    loadProgress();
  }, [recordingId]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current);
      }
    };
  }, []);

  const doSave = useCallback(
    async (positionSeconds: number, durationSeconds: number) => {
      if (!recordingId || durationSeconds <= 0) return;

      setIsSaving(true);
      const { data, error: apiError } = await saveProgress(
        recordingId,
        positionSeconds,
        durationSeconds
      );

      if (data) {
        setProgress((prev) => ({
          positionSeconds,
          durationSeconds,
          percentComplete: data.percentComplete,
          completed: data.completed,
          lastWatchedAt: new Date().toISOString(),
        }));
        lastSavedPositionRef.current = positionSeconds;
        lastSaveTimeRef.current = Date.now();
      } else if (apiError) {
        setError(apiError);
      }
      setIsSaving(false);
    },
    [recordingId]
  );

  /**
   * Save progress with debouncing logic.
   * Called on timeupdate, pause, and seek events.
   */
  const saveCurrentProgress = useCallback(
    (positionSeconds: number, durationSeconds: number) => {
      const now = Date.now();
      const timeSinceLastSave = now - lastSaveTimeRef.current;
      const seekDelta = Math.abs(
        positionSeconds - lastSavedPositionRef.current
      );

      // Immediate save on significant seek
      if (seekDelta >= SEEK_THRESHOLD_S && timeSinceLastSave > 2000) {
        if (saveTimerRef.current) {
          clearTimeout(saveTimerRef.current);
          saveTimerRef.current = null;
        }
        doSave(positionSeconds, durationSeconds);
        return;
      }

      // Debounced periodic save
      if (timeSinceLastSave >= SAVE_INTERVAL_MS) {
        if (saveTimerRef.current) {
          clearTimeout(saveTimerRef.current);
          saveTimerRef.current = null;
        }
        doSave(positionSeconds, durationSeconds);
      } else if (!saveTimerRef.current) {
        const remaining = SAVE_INTERVAL_MS - timeSinceLastSave;
        saveTimerRef.current = setTimeout(() => {
          saveTimerRef.current = null;
          doSave(positionSeconds, durationSeconds);
        }, remaining);
      }
    },
    [doSave]
  );

  return { progress, isLoading, error, saveCurrentProgress, isSaving };
}

/**
 * Hook to manage a playback token for a recording.
 *
 * @param recordingId - The recording identifier.
 * @returns Token, expiry, loading state, and refresh function.
 */
export function usePlaybackToken(
  recordingId: string
): UsePlaybackTokenReturn {
  const [token, setToken] = useState<string | null>(null);
  const [expiresInSeconds, setExpiresInSeconds] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchToken = useCallback(async () => {
    if (!recordingId) return;

    setIsLoading(true);
    setError(null);

    const { data, error: apiError } = await requestPlaybackToken(recordingId);

    if (data) {
      setToken(data.token);
      setExpiresInSeconds(data.expiresInSeconds);
    } else {
      setError(apiError || 'Failed to get playback token');
    }

    setIsLoading(false);
  }, [recordingId]);

  useEffect(() => {
    fetchToken();
  }, [fetchToken]);

  return { token, expiresInSeconds, isLoading, error, refresh: fetchToken };
}
