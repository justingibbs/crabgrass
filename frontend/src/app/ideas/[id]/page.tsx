"use client";

import { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { Header } from "@/components/layout";
import { IdeaCanvas, SimilarIdeasPanel } from "@/components/ideas";
import { api } from "@/lib/api";
import type { IdeaDetail } from "@/lib/types";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function IdeaDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const router = useRouter();
  const [idea, setIdea] = useState<IdeaDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadIdea = async () => {
    try {
      setIsLoading(true);
      const data = await api.ideas.get(id);
      setIdea(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load idea");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadIdea();
  }, [id]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col bg-background">
        <Header showBack />
        <div className="flex flex-1 items-center justify-center">
          <p className="text-muted-foreground">Loading idea...</p>
        </div>
      </div>
    );
  }

  if (error || !idea) {
    return (
      <div className="flex min-h-screen flex-col bg-background">
        <Header showBack />
        <div className="flex flex-1 items-center justify-center">
          <div className="text-center">
            <p className="text-destructive">{error || "Idea not found"}</p>
            <button
              onClick={() => router.push("/")}
              className="mt-4 text-sm text-muted-foreground underline"
            >
              Return to dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Header title={idea.title} status={idea.status} showBack />

      <div className="flex flex-1 overflow-hidden">
        <div className="flex w-full">
          <div className="flex-1 overflow-hidden border-r">
            <IdeaCanvas idea={idea} onUpdate={loadIdea} />
          </div>

          <div className="w-[350px] flex-shrink-0">
            <div className="flex h-full flex-col">
              <div className="border-b p-3">
                <SimilarIdeasPanel ideaId={id} />
              </div>

              <div className="flex-1">
                <CopilotSidebar
                  className="h-full border-none"
                  instructions={`You are helping the user refine their idea titled "${idea.title}".

Current idea state:
- Summary: ${idea.summary?.content || "Not set"}
- Challenge: ${idea.challenge?.content || "Not set"}
- Approach: ${idea.approach?.content || "Not set"}
- Actions: ${idea.coherent_actions.length} defined

Help them improve any section. When they ask to update or save changes, use the save_idea tool with idea_id="${id}".`}
                  labels={{
                    title: "Idea Assistant",
                    initial:
                      "I can help you refine this idea. What would you like to work on?",
                    placeholder: "Ask for suggestions or help with any section...",
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
