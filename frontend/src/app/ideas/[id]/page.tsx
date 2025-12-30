"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { IdeaCanvas } from "@/components/ideas/IdeaCanvas";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { SimilarIdeasPanel } from "@/components/ideas/SimilarIdeasPanel";
import { api } from "@/lib/api";
import type { IdeaDetail, Suggestion } from "@/lib/types";

export default function IdeaDetailPage() {
  const params = useParams();
  const ideaId = params.id as string;

  const [idea, setIdea] = useState<IdeaDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [similarRefreshTrigger, setSimilarRefreshTrigger] = useState(0);

  // Suggestions state - maps field to pending suggestion
  const [suggestions, setSuggestions] = useState<{
    summary?: Suggestion | null;
    challenge?: Suggestion | null;
    approach?: Suggestion | null;
  }>({});

  const fetchIdea = useCallback(async () => {
    try {
      const data = await api.ideas.get(ideaId);
      setIdea(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load idea");
    } finally {
      setLoading(false);
    }
  }, [ideaId]);

  // Handle content updates - refresh idea and trigger similar ideas refresh
  const handleContentUpdate = useCallback(async () => {
    await fetchIdea();
    // Increment trigger to refresh similar ideas panel
    setSimilarRefreshTrigger((prev) => prev + 1);
  }, [fetchIdea]);

  // Handle incoming suggestion from agent
  const handleSuggestion = useCallback((suggestion: Suggestion) => {
    setSuggestions((prev) => ({
      ...prev,
      [suggestion.field]: suggestion,
    }));
  }, []);

  // Accept a suggestion - save it via API and clear from pending
  const handleAcceptSuggestion = useCallback(
    async (field: Suggestion["field"]) => {
      const suggestion = suggestions[field];
      if (!suggestion || !idea) return;

      try {
        // Save the suggestion content to the appropriate field
        switch (field) {
          case "summary":
            if (idea.summary) {
              await api.summaries.update(idea.id, suggestion.content);
            } else {
              await api.summaries.create(idea.id, suggestion.content);
            }
            break;
          case "challenge":
            if (idea.challenge) {
              await api.challenges.update(idea.id, suggestion.content);
            } else {
              await api.challenges.create(idea.id, suggestion.content);
            }
            break;
          case "approach":
            if (idea.approach) {
              await api.approaches.update(idea.id, suggestion.content);
            } else {
              await api.approaches.create(idea.id, suggestion.content);
            }
            break;
        }

        // Clear the suggestion and refresh
        setSuggestions((prev) => ({
          ...prev,
          [field]: null,
        }));
        await fetchIdea();
        setSimilarRefreshTrigger((prev) => prev + 1);
      } catch (e) {
        console.error("Failed to accept suggestion:", e);
      }
    },
    [suggestions, idea, fetchIdea]
  );

  // Reject a suggestion - just clear it from pending
  const handleRejectSuggestion = useCallback((field: Suggestion["field"]) => {
    setSuggestions((prev) => ({
      ...prev,
      [field]: null,
    }));
  }, []);

  useEffect(() => {
    fetchIdea();
  }, [fetchIdea]);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header title="Loading..." />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-muted-foreground">Loading idea...</div>
        </main>
      </div>
    );
  }

  if (error || !idea) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header title="Error" />
        <main className="flex-1 flex flex-col items-center justify-center gap-4">
          <div className="text-red-500">{error || "Idea not found"}</div>
          <Link
            href="/"
            className="flex items-center gap-2 text-primary hover:underline"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Ideas
          </Link>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header title={idea.title} />
      <main className="flex-1 flex overflow-hidden">
        {/* Canvas - 70% */}
        <div className="w-[70%] border-r border-border p-6 overflow-y-auto">
          <div className="flex items-center gap-4 mb-6">
            <Link
              href="/"
              className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </Link>
            <StatusBadge status={idea.status} />
          </div>
          <IdeaCanvas
            idea={idea}
            onUpdate={handleContentUpdate}
            suggestions={suggestions}
            onAcceptSuggestion={handleAcceptSuggestion}
            onRejectSuggestion={handleRejectSuggestion}
          />
        </div>

        {/* Chat + Similar Ideas - 30% */}
        <div className="w-[30%] flex flex-col">
          <ChatPanel
            className="flex-1"
            ideaId={ideaId}
            onContextUpdate={() => handleContentUpdate()}
            onSuggestion={handleSuggestion}
          />
          <SimilarIdeasPanel
            ideaId={ideaId}
            refreshTrigger={similarRefreshTrigger}
          />
        </div>
      </main>
    </div>
  );
}

function StatusBadge({ status }: { status: IdeaDetail["status"] }) {
  const styles = {
    Draft: "bg-yellow-100 text-yellow-800",
    Active: "bg-green-100 text-green-800",
    Archived: "bg-gray-100 text-gray-800",
  };

  return (
    <span className={`px-2 py-1 text-xs rounded-full ${styles[status]}`}>
      {status}
    </span>
  );
}
