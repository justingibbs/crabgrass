"use client";

import { formatDistanceToNow } from "date-fns";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { IdeaListItem } from "@/lib/types";

interface IdeaCardProps {
  idea: IdeaListItem;
  onClick: () => void;
}

export function IdeaCard({ idea, onClick }: IdeaCardProps) {
  const timeAgo = idea.created_at
    ? formatDistanceToNow(new Date(idea.created_at), { addSuffix: true })
    : "recently";

  return (
    <Card
      className="cursor-pointer transition-colors hover:bg-accent/50"
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-4">
          <h3 className="font-semibold leading-none">{idea.title}</h3>
          <Badge
            variant={
              idea.status === "Active"
                ? "default"
                : idea.status === "Draft"
                  ? "secondary"
                  : "outline"
            }
          >
            {idea.status}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          {idea.author_name} · {timeAgo}
        </p>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground line-clamp-2">
          &ldquo;{idea.summary_preview}&rdquo;
        </p>
      </CardContent>
    </Card>
  );
}
