"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { ObjectiveListItem } from "@/lib/types";
import { ObjectiveCard } from "./ObjectiveCard";

export function ObjectivesList() {
  const router = useRouter();
  const [objectives, setObjectives] = useState<ObjectiveListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchObjectives() {
      try {
        const data = await api.objectives.list();
        setObjectives(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load objectives");
      } finally {
        setLoading(false);
      }
    }
    fetchObjectives();
  }, []);

  if (loading) {
    return (
      <div className="text-center py-8 text-muted-foreground text-sm">
        Loading objectives...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-500 text-sm">{error}</div>
    );
  }

  if (objectives.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground text-sm">
        <p>No objectives yet.</p>
        <p className="mt-1">Senior users can create objectives.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {objectives.map((objective) => (
        <ObjectiveCard
          key={objective.id}
          objective={objective}
          onClick={() => router.push(`/objectives/${objective.id}`)}
        />
      ))}
    </div>
  );
}
