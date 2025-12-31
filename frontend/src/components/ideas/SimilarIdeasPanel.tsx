"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sparkles, RefreshCw, ExternalLink } from "lucide-react";
import { api } from "@/lib/api";
import type { SimilarIdea } from "@/lib/types";
import { cn } from "@/lib/utils";

interface SimilarIdeasPanelProps {
  ideaId: string;
  refreshTrigger?: number; // Increment to trigger refresh
  className?: string;
}

export function SimilarIdeasPanel({
  ideaId,
  refreshTrigger = 0,
  className,
}: SimilarIdeasPanelProps) {
  const [similarIdeas, setSimilarIdeas] = useState<SimilarIdea[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSimilar = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.ideas.similar(ideaId, 5);
      setSimilarIdeas(data);
    } catch (e) {
      setError("Failed to load similar ideas");
      console.error("Error fetching similar ideas:", e);
    } finally {
      setLoading(false);
    }
  };

  // Fetch on mount and when refreshTrigger changes
  useEffect(() => {
    fetchSimilar();
  }, [ideaId, refreshTrigger]);

  const formatSimilarity = (similarity: number) => {
    return `${Math.round(similarity * 100)}%`;
  };

  return (
    <div
      className={cn(
        "border-t border-border bg-muted/30",
        className
      )}
      data-testid="similar-ideas-panel"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border/50">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium">Similar Ideas</span>
        </div>
        <button
          onClick={fetchSimilar}
          disabled={loading}
          className="p-1 hover:bg-muted rounded transition-colors disabled:opacity-50"
          title="Refresh similar ideas"
          data-testid="refresh-similar-ideas"
        >
          <RefreshCw className={cn("w-3 h-3", loading && "animate-spin")} />
        </button>
      </div>

      {/* Content */}
      <div className="max-h-48 overflow-y-auto">
        {loading && similarIdeas.length === 0 && (
          <div className="p-4 text-center text-sm text-muted-foreground">
            Loading similar ideas...
          </div>
        )}

        {error && (
          <div className="p-4 text-center text-sm text-red-500">{error}</div>
        )}

        {!loading && !error && similarIdeas.length === 0 && (
          <div className="p-4 text-center text-sm text-muted-foreground">
            No similar ideas found yet. Add more content to find connections.
          </div>
        )}

        {similarIdeas.length > 0 && (
          <ul className="divide-y divide-border/50">
            {similarIdeas.map((idea) => (
              <li key={idea.idea_id} data-testid="similar-idea-item">
                <Link
                  href={`/ideas/${idea.idea_id}`}
                  className="flex items-start gap-3 p-3 hover:bg-muted/50 transition-colors group"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate group-hover:text-primary transition-colors">
                      {idea.title}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatSimilarity(idea.similarity)} similar
                    </p>
                  </div>
                  <ExternalLink className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 mt-1" />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
