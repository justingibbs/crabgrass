"use client";

import { useRouter } from "next/navigation";
import { IdeaCard } from "./IdeaCard";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { IdeaListItem } from "@/lib/types";

interface IdeaListProps {
  ideas: IdeaListItem[];
  isLoading?: boolean;
}

export function IdeaList({ ideas, isLoading }: IdeaListProps) {
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-muted-foreground">Loading ideas...</div>
      </div>
    );
  }

  if (ideas.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <p className="text-muted-foreground">No ideas yet.</p>
        <p className="text-sm text-muted-foreground">
          Click &ldquo;New Idea&rdquo; to capture your first idea.
        </p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-[calc(100vh-200px)]">
      <div className="grid gap-4 pr-4">
        {ideas.map((idea) => (
          <IdeaCard
            key={idea.id}
            idea={idea}
            onClick={() => router.push(`/ideas/${idea.id}`)}
          />
        ))}
      </div>
    </ScrollArea>
  );
}
