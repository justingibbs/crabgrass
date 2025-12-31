"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "@/lib/api";
import type { Notification } from "@/lib/types";

interface UseNotificationsOptions {
  /** Poll interval in milliseconds (default: 5000) */
  pollInterval?: number;
  /** Enable SSE streaming (default: true) */
  enableSSE?: boolean;
  /** Initial limit for notifications (default: 50) */
  limit?: number;
}

interface UseNotificationsReturn {
  notifications: Notification[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  clearAll: () => Promise<void>;
}

/**
 * Hook for fetching and streaming notifications.
 *
 * Combines initial polling with SSE for real-time updates.
 * Falls back to polling if SSE connection fails.
 */
export function useNotifications(
  options: UseNotificationsOptions = {}
): UseNotificationsReturn {
  const { pollInterval = 5000, enableSSE = true, limit = 50 } = options;

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch all notifications
  const fetchNotifications = useCallback(async () => {
    try {
      const data = await api.notifications.listAll(limit);
      setNotifications(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load notifications");
    } finally {
      setLoading(false);
    }
  }, [limit]);

  // Handle new notification from SSE
  const handleNewNotification = useCallback((notification: Notification) => {
    setNotifications((prev) => {
      // Check if notification already exists
      if (prev.some((n) => n.id === notification.id)) {
        return prev;
      }
      // Add to beginning (newest first)
      return [notification, ...prev];
    });
  }, []);

  // Set up SSE connection
  const setupSSE = useCallback(() => {
    if (!enableSSE || typeof window === "undefined") return;

    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource(api.notifications.streamUrl());
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const notification = JSON.parse(event.data) as Notification;
        handleNewNotification(notification);
      } catch {
        // Ignore parse errors (heartbeats, etc.)
      }
    };

    eventSource.onerror = () => {
      // On error, close and fall back to polling
      eventSource.close();
      eventSourceRef.current = null;

      // Set up polling fallback
      if (!pollIntervalRef.current) {
        pollIntervalRef.current = setInterval(fetchNotifications, pollInterval);
      }
    };

    return () => {
      eventSource.close();
    };
  }, [enableSSE, handleNewNotification, fetchNotifications, pollInterval]);

  // Refresh notifications manually
  const refresh = useCallback(async () => {
    setLoading(true);
    await fetchNotifications();
  }, [fetchNotifications]);

  // Clear all notifications
  const clearAll = useCallback(async () => {
    try {
      await api.notifications.clearAll();
      setNotifications([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to clear notifications");
    }
  }, []);

  // Initial fetch and SSE setup
  useEffect(() => {
    fetchNotifications();
    const cleanupSSE = setupSSE();

    // Also set up polling as backup (less frequent when SSE is active)
    pollIntervalRef.current = setInterval(
      fetchNotifications,
      enableSSE ? pollInterval * 2 : pollInterval
    );

    return () => {
      cleanupSSE?.();
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [fetchNotifications, setupSSE, enableSSE, pollInterval]);

  return {
    notifications,
    loading,
    error,
    refresh,
    clearAll,
  };
}
