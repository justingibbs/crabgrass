"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Eye, EyeOff, Users, FileText } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { api } from "@/lib/api";
import type { ObjectiveDetail, LinkedIdea } from "@/lib/types";
import { cn } from "@/lib/utils";

function StatusBadge({ status }: { status: "Active" | "Retired" }) {
  return (
    <span
      className={cn(
        "px-2 py-1 text-xs rounded-full",
        status === "Active" && "bg-green-100 text-green-800",
        status === "Retired" && "bg-gray-100 text-gray-800"
      )}
    >
      {status}
    </span>
  );
}

export default function ObjectiveDetailPage() {
  const params = useParams();
  const router = useRouter();
  const objectiveId = params.id as string;

  const [objective, setObjective] = useState<ObjectiveDetail | null>(null);
  const [linkedIdeas, setLinkedIdeas] = useState<LinkedIdea[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [objData, ideasData] = await Promise.all([
          api.objectives.get(objectiveId),
          api.objectives.getLinkedIdeas(objectiveId),
        ]);
        setObjective(objData);
        setLinkedIdeas(ideasData);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load objective");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [objectiveId]);

  const handleWatch = async () => {
    if (!objective) return;
    try {
      if (objective.is_watched) {
        await api.objectives.unwatch(objectiveId);
        setObjective({ ...objective, is_watched: false });
      } else {
        await api.objectives.watch(objectiveId);
        setObjective({ ...objective, is_watched: true });
      }
    } catch (e) {
      console.error("Failed to update watch status:", e);
    }
  };

  const handleRetire = async () => {
    if (!objective || objective.status === "Retired") return;
    if (!confirm("Are you sure you want to retire this objective?")) return;

    try {
      const updated = await api.objectives.retire(objectiveId);
      setObjective(updated);
    } catch (e) {
      console.error("Failed to retire objective:", e);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header title="Objective" />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-muted-foreground">Loading...</div>
        </main>
      </div>
    );
  }

  if (error || !objective) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header title="Objective" />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-red-500">{error || "Objective not found"}</div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header title={objective.title} />
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-6">
        {/* Back button */}
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>

        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold">{objective.title}</h1>
              <StatusBadge status={objective.status} />
            </div>
            <p className="text-sm text-muted-foreground">
              Created by {objective.author_name}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleWatch}
              className={cn(
                "flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-colors",
                objective.is_watched
                  ? "border-primary text-primary"
                  : "border-border hover:bg-muted"
              )}
            >
              {objective.is_watched ? (
                <>
                  <EyeOff className="w-4 h-4" />
                  Unwatch
                </>
              ) : (
                <>
                  <Eye className="w-4 h-4" />
                  Watch
                </>
              )}
            </button>

            {objective.status === "Active" && (
              <button
                onClick={handleRetire}
                className="px-3 py-1.5 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
              >
                Retire
              </button>
            )}
          </div>
        </div>

        {/* Description */}
        <div className="bg-card border rounded-lg p-4 mb-6">
          <h2 className="text-sm font-medium text-muted-foreground mb-2">
            Description
          </h2>
          <p className="whitespace-pre-wrap">{objective.description}</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-card border rounded-lg p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <FileText className="w-5 h-5 text-primary" />
            </div>
            <div>
              <div className="text-2xl font-bold">{objective.idea_count}</div>
              <div className="text-sm text-muted-foreground">Linked Ideas</div>
            </div>
          </div>
          <div className="bg-card border rounded-lg p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Users className="w-5 h-5 text-primary" />
            </div>
            <div>
              <div className="text-2xl font-bold">
                {objective.sub_objective_count}
              </div>
              <div className="text-sm text-muted-foreground">
                Sub-Objectives
              </div>
            </div>
          </div>
        </div>

        {/* Linked Ideas */}
        <div className="bg-card border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-4">Linked Ideas</h2>
          {linkedIdeas.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              No ideas linked to this objective yet.
            </p>
          ) : (
            <div className="space-y-2">
              {linkedIdeas.map((idea) => (
                <Link
                  key={idea.idea_id}
                  href={`/ideas/${idea.idea_id}`}
                  className="block p-3 rounded-lg border hover:bg-accent transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{idea.title}</span>
                    <span
                      className={cn(
                        "px-2 py-0.5 text-xs rounded-full",
                        idea.status === "Active" && "bg-green-100 text-green-800",
                        idea.status === "Draft" && "bg-yellow-100 text-yellow-800",
                        idea.status === "Archived" && "bg-gray-100 text-gray-800"
                      )}
                    >
                      {idea.status}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
