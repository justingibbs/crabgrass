"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Header } from "@/components/layout";
import { IdeaList } from "@/components/ideas";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { IdeaListItem } from "@/lib/types";

export default function HomePage() {
  const [ideas, setIdeas] = useState<IdeaListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadIdeas() {
      try {
        setIsLoading(true);
        const data = await api.ideas.list();
        setIdeas(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load ideas");
      } finally {
        setIsLoading(false);
      }
    }

    loadIdeas();

    const handleFocus = () => {
      loadIdeas();
    };

    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container py-6">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Your Ideas</h1>
          <Link href="/ideas/new">
            <Button>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="mr-2"
              >
                <path d="M12 5v14M5 12h14" />
              </svg>
              New Idea
            </Button>
          </Link>
        </div>

        {error ? (
          <div className="rounded-lg border border-destructive bg-destructive/10 p-4 text-destructive">
            {error}
          </div>
        ) : (
          <IdeaList ideas={ideas} isLoading={isLoading} />
        )}
      </main>
    </div>
  );
}
