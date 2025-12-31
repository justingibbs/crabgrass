"use client";

import { useRouter } from "next/navigation";
import type { IdeaListItem } from "@/lib/types";
import { IdeaCard } from "./IdeaCard";

interface IdeaListProps {
  ideas: IdeaListItem[];
}

export function IdeaList({ ideas }: IdeaListProps) {
  const router = useRouter();

  if (ideas.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p>No ideas yet.</p>
        <p className="text-sm mt-1">Click "New Idea" to get started.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {ideas.map((idea) => (
        <IdeaCard
          key={idea.id}
          idea={idea}
          onClick={() => router.push(`/ideas/${idea.id}`)}
        />
      ))}
    </div>
  );
}
