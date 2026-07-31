'use client';

import { useCallback, useRef, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { apiClient } from '@/lib/api';
import type { DangerAction } from './types';

// ---------------------------------------------------------------------------
// Danger actions defined internally
// ---------------------------------------------------------------------------

const actions: DangerAction[] = [
  {
    id: 'reset-progress',
    name: 'Reset All Progress',
    description:
      'Permanently delete all learning progress for your account. This cannot be undone.',
    confirmPhrase: 'RESET ALL PROGRESS',
    onExecute: async () => {
      const { error } = await apiClient.resetProgress();
      if (error) throw new Error(error);
      await apiClient.logout();
      sessionStorage.clear();
      window.location.href = '/';
    },
  },
];

// ---------------------------------------------------------------------------
// DangerZone component
// ---------------------------------------------------------------------------

export function DangerZone() {
  const [activeActionId, setActiveActionId] = useState<string | null>(null);
  const [typedPhrase, setTypedPhrase] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const errorTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleTrigger = useCallback((actionId: string) => {
    setActiveActionId(actionId);
    setTypedPhrase('');
    setError(null);
  }, []);

  const handleCancel = useCallback(() => {
    setActiveActionId(null);
    setTypedPhrase('');
    setError(null);
  }, []);

  const handleConfirm = useCallback(
    async (action: DangerAction) => {
      if (typedPhrase !== action.confirmPhrase) return;

      setIsExecuting(true);
      setError(null);

      try {
        await action.onExecute();
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : 'An unexpected error occurred';
        setError(message);
        // Re-enable triggers within 1 second
        if (errorTimeoutRef.current) {
          clearTimeout(errorTimeoutRef.current);
        }
        errorTimeoutRef.current = setTimeout(() => {
          setIsExecuting(false);
        }, 1000);
        return;
      }

      setIsExecuting(false);
      setActiveActionId(null);
      setTypedPhrase('');
    },
    [typedPhrase]
  );

  return (
    <Card
      className="border-red-200 dark:border-red-800 bg-red-50/30 dark:bg-red-950/20"
      padding="lg"
    >
      {/* Section heading */}
      <div className="flex items-center gap-2 mb-6">
        <svg
          className="w-5 h-5 text-red-600 dark:text-red-400"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
          />
        </svg>
        <h2 className="text-lg font-semibold text-red-900 dark:text-red-100">
          Danger Zone
        </h2>
      </div>

      {/* Error message */}
      {error && (
        <div
          className="mb-4 p-3 rounded-lg bg-red-100 dark:bg-red-900/40 border border-red-300 dark:border-red-700 text-red-800 dark:text-red-200 text-sm"
          role="alert"
        >
          {error}
        </div>
      )}

      {/* Action list */}
      <div className="space-y-4">
        {actions.map((action) => (
          <DangerActionItem
            key={action.id}
            action={action}
            isActive={activeActionId === action.id}
            isExecuting={isExecuting}
            typedPhrase={activeActionId === action.id ? typedPhrase : ''}
            onTrigger={handleTrigger}
            onCancel={handleCancel}
            onConfirm={handleConfirm}
            onPhraseChange={setTypedPhrase}
          />
        ))}
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Individual action item
// ---------------------------------------------------------------------------

interface DangerActionItemProps {
  action: DangerAction;
  isActive: boolean;
  isExecuting: boolean;
  typedPhrase: string;
  onTrigger: (actionId: string) => void;
  onCancel: () => void;
  onConfirm: (action: DangerAction) => void;
  onPhraseChange: (value: string) => void;
}

function DangerActionItem({
  action,
  isActive,
  isExecuting,
  typedPhrase,
  onTrigger,
  onCancel,
  onConfirm,
  onPhraseChange,
}: DangerActionItemProps) {
  const phraseMatches = typedPhrase === action.confirmPhrase;

  return (
    <div className="rounded-lg border border-red-100 dark:border-red-900 p-4">
      {/* Action header row */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900 dark:text-gray-100">
            {action.name}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
            {action.description}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {isExecuting && isActive && <Spinner size="sm" />}
          <Button
            variant="danger"
            size="sm"
            disabled={isExecuting}
            onClick={() => onTrigger(action.id)}
            aria-expanded={isActive}
            aria-controls={`confirm-panel-${action.id}`}
          >
            {action.name}
          </Button>
        </div>
      </div>

      {/* Inline confirmation panel (two-step) */}
      {isActive && (
        <div
          id={`confirm-panel-${action.id}`}
          className="mt-4 p-4 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800"
          role="region"
          aria-label={`Confirm ${action.name}`}
        >
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">
            This action is irreversible.
          </p>
          <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
            Type{' '}
            <code className="px-1.5 py-0.5 rounded bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 font-mono text-xs">
              {action.confirmPhrase}
            </code>{' '}
            to confirm.
          </p>

          <input
            type="text"
            className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
            placeholder={action.confirmPhrase}
            value={typedPhrase}
            onChange={(e) => onPhraseChange(e.target.value)}
            disabled={isExecuting}
            aria-label={`Type ${action.confirmPhrase} to confirm`}
            autoComplete="off"
            spellCheck={false}
          />

          <div className="flex items-center gap-3 mt-3">
            <Button
              variant="danger"
              size="sm"
              disabled={!phraseMatches || isExecuting}
              onClick={() => onConfirm(action)}
            >
              {isExecuting ? 'Processing…' : 'Confirm'}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              disabled={isExecuting}
              onClick={onCancel}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
