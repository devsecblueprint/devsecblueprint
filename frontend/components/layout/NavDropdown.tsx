'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { usePathname } from 'next/navigation';

export interface NavDropdownProps {
  items: { label: string; href: string; icon?: React.ReactNode }[];
  label: string;
  isActive: boolean;
  isMobile?: boolean;
  onNavigate?: () => void;
}

/**
 * NavDropdown component for the About section navigation.
 * Desktop: hover/click-triggered dropdown with outside-click and Escape dismiss.
 * Mobile: expandable section within the mobile menu.
 */
export function NavDropdown({
  items,
  label,
  isActive,
  isMobile = false,
  onNavigate,
}: NavDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();

  // Check if a specific item matches the current URL
  const isItemActive = (href: string) => {
    if (!pathname) return false;
    if (href === '/about') {
      return pathname === '/about';
    }
    return pathname.startsWith(href);
  };

  // Close dropdown on outside click (desktop only)
  useEffect(() => {
    if (isMobile || !isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, isMobile]);

  // Close dropdown on Escape key (desktop only)
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false);
        event.preventDefault();
      }
    },
    [isOpen]
  );

  // Mobile variant: expandable section
  if (isMobile) {
    return (
      <div className="py-1">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`flex items-center justify-between w-full py-2 text-sm font-medium transition-colors ${
            isActive
              ? 'text-primary-500 dark:text-primary-400'
              : 'text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400'
          }`}
          aria-haspopup="true"
          aria-expanded={isOpen}
        >
          <span className="flex items-center space-x-2">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>{label}</span>
          </span>
          <svg
            className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>

        {isOpen && (
          <div role="menu" className="pl-7 mt-1 space-y-1">
            {items.map((item) => (
              <a
                key={item.href}
                href={item.href}
                role="menuitem"
                onClick={() => {
                  onNavigate?.();
                }}
                className={`flex items-center py-2 text-sm transition-colors ${
                  isItemActive(item.href)
                    ? 'text-primary-500 dark:text-primary-400'
                    : 'text-gray-600 dark:text-gray-400 hover:text-primary-400 dark:hover:text-primary-400'
                }`}
              >
                {item.icon && <span className="mr-2 flex-shrink-0" aria-hidden="true">{item.icon}</span>}
                {item.label}
              </a>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Desktop variant: hover/click-triggered dropdown
  return (
    <div
      ref={dropdownRef}
      className="relative"
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
      onKeyDown={handleKeyDown}
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`inline-flex items-center space-x-1 text-sm font-medium transition-colors ${
          isActive
            ? 'text-primary-500 dark:text-primary-400'
            : 'text-gray-700 dark:text-gray-300 hover:text-primary-400 dark:hover:text-primary-400'
        }`}
        aria-haspopup="true"
        aria-expanded={isOpen}
      >
        <span>{label}</span>
        <svg
          className={`w-3.5 h-3.5 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 pt-2 z-50">
          <div
            role="menu"
            className="w-48 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg shadow-lg py-2"
          >
            {items.map((item) => (
              <a
                key={item.href}
                href={item.href}
                role="menuitem"
                onClick={() => {
                  setIsOpen(false);
                  onNavigate?.();
                }}
                className={`flex items-center px-4 py-2 text-sm transition-colors ${
                  isItemActive(item.href)
                    ? 'text-primary-500 dark:text-primary-400'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-primary-400 dark:hover:text-primary-400'
                }`}
              >
                {item.icon && <span className="mr-2 flex-shrink-0" aria-hidden="true">{item.icon}</span>}
                {item.label}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
