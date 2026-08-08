'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';

export interface SearchBarProps {
  value: string;
  onChange: (query: string) => void;
  resultCount: number;
  placeholder?: string;
}

/**
 * Search input with internal debounce for filtering FAQ questions.
 * Manages its own input display state while the parent controls the debounced
 * value used for filtering. Includes sticky positioning on mobile, accessible
 * aria-live region for result announcements, clear button, and search icon.
 *
 * @param value - The debounced/parent-controlled search value (used for aria-live count)
 * @param onChange - Callback invoked with debounced input value (150ms delay)
 * @param resultCount - Number of matching questions (announced via aria-live)
 * @param placeholder - Input placeholder text (default: "Search questions...")
 */
export function SearchBar({
  value,
  onChange,
  resultCount,
  placeholder = 'Search questions...',
}: SearchBarProps) {
  const [inputValue, setInputValue] = useState(value);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync internal state when parent value changes externally (e.g., clear from parent)
  useEffect(() => {
    setInputValue(value);
  }, [value]);

  const debouncedOnChange = useCallback(
    (newValue: string) => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
      debounceRef.current = setTimeout(() => {
        onChange(newValue);
      }, 150);
    },
    [onChange]
  );

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    debouncedOnChange(newValue);
  };

  const handleClear = () => {
    setInputValue('');
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    onChange('');
  };

  const resultAnnouncement =
    value.length > 0
      ? `${resultCount} question${resultCount !== 1 ? 's' : ''} found`
      : '';

  return (
    <div className="sticky top-[64px] z-10 sm:static bg-white dark:bg-gray-950 pb-4">
      <div className="relative">
        {/* Search icon */}
        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
          <svg
            className="h-5 w-5 text-gray-400 dark:text-gray-500"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z"
              clipRule="evenodd"
            />
          </svg>
        </div>

        {/* Input */}
        <input
          type="search"
          value={inputValue}
          onChange={handleInputChange}
          placeholder={placeholder}
          aria-label="Search FAQ questions"
          className="block w-full rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 py-3 pl-10 pr-10 text-base text-gray-900 dark:text-gray-100 placeholder:text-gray-500 dark:placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400 focus:border-transparent transition-colors"
        />

        {/* Clear button */}
        {inputValue.length > 0 && (
          <button
            type="button"
            onClick={handleClear}
            aria-label="Clear search"
            className="absolute inset-y-0 right-0 flex items-center pr-3 pl-2 min-w-[44px] text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors"
          >
            <svg
              className="h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        )}
      </div>

      {/* Aria-live region for screen reader announcements */}
      <span
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {resultAnnouncement}
      </span>
    </div>
  );
}
