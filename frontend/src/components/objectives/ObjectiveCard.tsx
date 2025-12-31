"use client";

import { cn } from "@/lib/utils";
import type { ObjectiveListItem } from "@/lib/types";

interface ObjectiveCardProps {
  objective: ObjectiveListItem;
  onClick?: () => void;
}

export function ObjectiveCard({ objective, onClick }: ObjectiveCardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors",
        onClick && "cursor-pointer"
      )}
    >
      <div className="flex items-start justify-between">
        <h3 className="font-medium text-sm">{objective.title}</h3>
        <StatusBadge status={objective.status} />
      </div>
      <p className="text-xs text-muted-foreground mt-1">
        {objective.idea_count} {objective.idea_count === 1 ? "Idea" : "Ideas"}
      </p>
    </div>
  );
}

function StatusBadge({ status }: { status: "Active" | "Retired" }) {
  return (
    <span
      className={cn(
        "px-2 py-0.5 text-xs rounded-full",
        status === "Active" && "bg-green-100 text-green-800",
        status === "Retired" && "bg-gray-100 text-gray-800"
      )}
    >
      {status}
    </span>
  );
}
