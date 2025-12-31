"use client";

import Link from "next/link";
import { Bell, Lightbulb, Link2, AlertTriangle, RefreshCw } from "lucide-react";
import { useNotifications } from "@/hooks/useNotifications";
import type { Notification, NotificationType } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * Get icon for notification type
 */
function getNotificationIcon(type: NotificationType) {
  switch (type) {
    case "similar_found":
      return <Bell className="w-4 h-4 text-blue-500" />;
    case "idea_linked":
      return <Link2 className="w-4 h-4 text-green-500" />;
    case "nurture_nudge":
      return <Lightbulb className="w-4 h-4 text-yellow-500" />;
    case "orphan_alert":
      return <AlertTriangle className="w-4 h-4 text-orange-500" />;
    case "contribution":
      return <Bell className="w-4 h-4 text-purple-500" />;
    case "reconnection_suggestion":
      return <RefreshCw className="w-4 h-4 text-teal-500" />;
    default:
      return <Bell className="w-4 h-4 text-gray-500" />;
  }
}

/**
 * Format relative time
 */
function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return "";

  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}

/**
 * Get link for notification based on source type
 */
function getNotificationLink(notification: Notification): string {
  if (notification.source_type === "idea") {
    return `/ideas/${notification.source_id}`;
  }
  if (notification.source_type === "objective") {
    return `/objectives/${notification.source_id}`;
  }
  // Default to idea if related_id exists
  if (notification.related_id) {
    return `/ideas/${notification.related_id}`;
  }
  return "#";
}

interface AlertCardProps {
  notification: Notification;
}

function AlertCard({ notification }: AlertCardProps) {
  const link = getNotificationLink(notification);

  return (
    <Link href={link}>
      <div
        className={cn(
          "p-3 rounded-lg border transition-colors hover:bg-accent cursor-pointer",
          notification.read ? "bg-background" : "bg-accent/30"
        )}
      >
        <div className="flex items-start gap-2">
          <div className="mt-0.5">{getNotificationIcon(notification.type)}</div>
          <div className="flex-1 min-w-0">
            <p className="text-sm leading-snug">{notification.message}</p>
            <p className="text-xs text-muted-foreground mt-1">
              {formatRelativeTime(notification.created_at)}
            </p>
          </div>
        </div>
      </div>
    </Link>
  );
}

export function SurfacedAlerts() {
  const { notifications, loading, error, clearAll } = useNotifications({
    pollInterval: 5000,
    enableSSE: true,
    limit: 50,
  });

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Surfaced Alerts</h2>
        {notifications.length > 0 && (
          <button
            onClick={() => clearAll()}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Clear all
          </button>
        )}
      </div>

      {loading && (
        <div className="text-center py-8 text-muted-foreground">
          Loading alerts...
        </div>
      )}

      {error && (
        <div className="text-center py-8 text-red-500 text-sm">{error}</div>
      )}

      {!loading && !error && notifications.length === 0 && (
        <div className="text-center py-8 text-muted-foreground text-sm">
          No alerts yet. Background agents will surface relevant insights here.
        </div>
      )}

      {!loading && !error && notifications.length > 0 && (
        <div className="flex flex-col gap-2 overflow-y-auto">
          {notifications.map((notification) => (
            <AlertCard key={notification.id} notification={notification} />
          ))}
        </div>
      )}
    </div>
  );
}
