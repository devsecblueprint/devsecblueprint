'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { NotificationDropdown } from './NotificationDropdown';
import type { NotificationData } from '@/lib/types';

/**
 * NotificationBell component
 * 
 * Bell icon displayed in the navbar for authenticated users.
 * Shows an unread count badge when there are pending notifications.
 * Clicking toggles the NotificationDropdown.
 * Fetches notifications via getNotifications on mount.
 * 
 * Accessible: aria-label describes notification state including unread count.
 */
export function NotificationBell() {
  const [notifications, setNotifications] = useState<NotificationData[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  const fetchNotifications = useCallback(async () => {
    const { data } = await apiClient.getNotifications();
    if (data?.notifications) {
      setNotifications(data.notifications);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handleAcknowledge = useCallback(async (notificationId: string, link: string) => {
    await apiClient.deleteNotification(notificationId);
    setNotifications(prev => prev.filter(n => n.notification_id !== notificationId));
    setIsOpen(false);
    window.location.href = link;
  }, []);

  const handleClose = useCallback(() => {
    setIsOpen(false);
  }, []);

  const unreadCount = notifications.length;

  const ariaLabel = unreadCount === 0
    ? 'Notifications, no unread notifications'
    : `Notifications, ${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}`;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400"
        aria-label={ariaLabel}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        {/* Bell icon */}
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
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>

        {/* Unread count badge */}
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 inline-flex items-center justify-center w-4 h-4 text-[10px] font-bold text-white bg-red-500 rounded-full">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notification dropdown */}
      {isOpen && (
        <NotificationDropdown
          notifications={notifications}
          onAcknowledge={handleAcknowledge}
          onClose={handleClose}
        />
      )}
    </div>
  );
}
