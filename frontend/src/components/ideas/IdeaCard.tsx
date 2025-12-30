"use client";

import { formatDistanceToNow } from "date-fns";
import type { IdeaListItem } from "@/lib/types";
import { cn } from "@/lib/utils";

interface IdeaCardProps {
  idea: IdeaListItem;
  onClick: () => void;
}

export function IdeaCard({ idea, onClick }: IdeaCardProps) {
  const timeAgo = idea.created_at
    ? formatDistanceToNow(new Date(idea.created_at), { addSuffix: true })
    : "";

  return (
    <button
      onClick={onClick}
      className="w-full text-left p-4 border border-border rounded-lg hover:border-primary/50 hover:bg-muted/50 transition-all"
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-medium">{idea.title}</h3>
        <StatusBadge status={idea.status} />
      </div>
      <p className="text-sm text-muted-foreground mt-1">
        {idea.author_name} · {timeAgo}
      </p>
      {idea.summary_preview && (
        <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
          "{idea.summary_preview}"
        </p>
      )}
    </button>
  );
}

function StatusBadge({ status }: { status: "Draft" | "Active" | "Archived" }) {
  return (
    <span
      className={cn(
        "px-2 py-0.5 text-xs rounded-full whitespace-nowrap",
        status === "Draft" && "bg-yellow-100 text-yellow-800",
        status === "Active" && "bg-green-100 text-green-800",
        status === "Archived" && "bg-gray-100 text-gray-800"
      )}
    >
      {status}
    </span>
  );
}
