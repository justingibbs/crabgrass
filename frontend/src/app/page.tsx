"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { useRole } from "@/components/layout/RoleToggle";
import { IdeaList } from "@/components/ideas/IdeaList";
import { ObjectivesList } from "@/components/objectives/ObjectivesList";
import { SurfacedAlerts } from "@/components/notifications/SurfacedAlerts";
import { api } from "@/lib/api";
import type { IdeaListItem } from "@/lib/types";

export default function HomePage() {
  const [ideas, setIdeas] = useState<IdeaListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const role = useRole();

  useEffect(() => {
    async function fetchData() {
      try {
        const ideasData = await api.ideas.list();
        setIdeas(ideasData);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const isSenior = role === "Senior";

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 px-4 py-6">
        {/* Action Buttons Row */}
        <div className="max-w-7xl mx-auto mb-6 flex items-center justify-between">
          <Link
            href="/ideas/new"
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Idea
          </Link>

          {isSenior && (
            <Link
              href="/objectives/new"
              className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Objective
            </Link>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="max-w-7xl mx-auto text-center py-8 text-muted-foreground">
            Loading...
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="max-w-7xl mx-auto text-center py-8 text-red-500">
            {error}
          </div>
        )}

        {/* 3-Column Layout */}
        {!loading && !error && (
          <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Left Column: IDEAS */}
            <div className="flex flex-col">
              <h2 className="text-lg font-semibold mb-4">Ideas</h2>
              <div className="flex-1 overflow-y-auto">
                <IdeaList ideas={ideas} />
              </div>
            </div>

            {/* Middle Column: OBJECTIVES */}
            <div className="flex flex-col">
              <h2 className="text-lg font-semibold mb-4">Objectives</h2>
              <div className="flex-1 overflow-y-auto">
                <ObjectivesList />
              </div>
            </div>

            {/* Right Column: SURFACED ALERTS */}
            <div className="flex flex-col">
              <SurfacedAlerts />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
