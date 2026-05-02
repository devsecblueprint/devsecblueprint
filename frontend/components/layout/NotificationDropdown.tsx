'use client';

import { useEffect, useRef, useCallback } from 'react';
import type { NotificationData } from '@/lib/types';

interface NotificationDropdownProps {
  notifications: NotificationData[];
  onAcknowledge: (notificationId: string, link: string) => void;
  onClose: () => void;
}

/**
 * NotificationDropdown component
 * 
 * Dropdown panel listing all notifications. All items are unread since
 * read ones are deleted from the database. Clicking a notification
 * acknowledges it (deletes from DB) and navigates to the linked page.
 * 
 * Accessible: role="menu", role="menuitem", keyboard navigable (arrow keys, Enter, Escape).
 * Closes on outside click.
 */
export function NotificationDropdown({ notifications, onAcknowledge, onClose }: NotificationDropdownProps) {
  const dropdownRef = useRef<HTMLDivElement>(null);
  const itemsRef = useRef<(HTMLButtonElement | null)[]>([]);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        onClose();
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  // Keyboard navigation
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    const items = itemsRef.current.filter(Boolean) as HTMLButtonElement[];
    const currentIndex = items.findIndex(item => item === document.activeElement);

    switch (event.key) {
      case 'ArrowDown': {
        event.preventDefault();
        const nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
        items[nextIndex]?.focus();
        break;
      }
      case 'ArrowUp': {
        event.preventDefault();
        const prevIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
        items[prevIndex]?.focus();
        break;
      }
      case 'Escape':
        event.preventDefault();
        onClose();
        break;
    }
  }, [onClose]);

  // Focus first item on mount
  useEffect(() => {
    const items = itemsRef.current.filter(Boolean) as HTMLButtonElement[];
    if (items.length > 0) {
      items[0].focus();
    }
  }, []);

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString();
    } catch {
      return '';
    }
  };

  return (
    <div
      ref={dropdownRef}
      role="menu"
      aria-label="Notifications"
      onKeyDown={handleKeyDown}
      className="absolute right-0 mt-2 w-80 max-h-96 overflow-y-auto bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg shadow-lg z-50"
    >
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800">
        <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">Notifications</p>
      </div>

      {notifications.length === 0 ? (
        <div className="px-4 py-8 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">No notifications yet</p>
        </div>
      ) : (
        <div className="py-1">
          {notifications.map((notification, index) => (
            <button
              key={notification.notification_id}
              ref={(el) => { itemsRef.current[index] = el; }}
              role="menuitem"
              onClick={() => onAcknowledge(notification.notification_id, notification.link)}
              className="w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors focus:outline-none focus:bg-gray-50 dark:focus:bg-gray-800 border-b border-gray-100 dark:border-gray-800 last:border-b-0"
            >
              <p className="text-sm text-gray-900 dark:text-gray-100 line-clamp-2">
                {notification.message}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {formatTimestamp(notification.created_at)}
              </p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
