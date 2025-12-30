"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { IdeaList } from "@/components/ideas/IdeaList";
import { api } from "@/lib/api";
import type { IdeaListItem } from "@/lib/types";

export default function HomePage() {
  const [ideas, setIdeas] = useState<IdeaListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchIdeas() {
      try {
        const data = await api.ideas.list();
        setIdeas(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load ideas");
      } finally {
        setLoading(false);
      }
    }
    fetchIdeas();
  }, []);

  return (
    <div className="min-h-screen">
      <Header />
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Your Ideas</h1>
          <Link
            href="/ideas/new"
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Idea
          </Link>
        </div>

        {loading && (
          <div className="text-center py-8 text-muted-foreground">
            Loading ideas...
          </div>
        )}

        {error && (
          <div className="text-center py-8 text-red-500">
            {error}
          </div>
        )}

        {!loading && !error && <IdeaList ideas={ideas} />}
      </main>
    </div>
  );
}
