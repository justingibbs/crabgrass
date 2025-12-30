"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { IdeaCanvas } from "@/components/ideas/IdeaCanvas";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { api } from "@/lib/api";
import type { IdeaDetail } from "@/lib/types";

export default function IdeaDetailPage() {
  const params = useParams();
  const ideaId = params.id as string;

  const [idea, setIdea] = useState<IdeaDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
          <IdeaCanvas idea={idea} onUpdate={fetchIdea} />
        </div>

        {/* Chat - 30% */}
        <div className="w-[30%] flex flex-col">
          <ChatPanel
            className="flex-1"
            instructions={`You are helping with an idea titled "${idea.title}". The user may want to refine the Summary, Challenge, Approach, or Coherent Actions. Guide them to improve their idea.`}
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
