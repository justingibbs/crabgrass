"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { ChatPanel } from "@/components/chat/ChatPanel";

export default function NewIdeaPage() {
  const router = useRouter();
  const [createdIdeaId, setCreatedIdeaId] = useState<string | null>(null);

  // TODO: Listen for idea creation from agent via state updates
  // For now, provide manual navigation buttons

  return (
    <div className="min-h-screen flex flex-col">
      <Header title="New Idea" />
      <main className="flex-1 flex flex-col max-w-4xl mx-auto w-full px-4 py-6">
        <div className="flex-1 border border-border rounded-lg overflow-hidden">
          <ChatPanel
            className="h-full min-h-[500px]"
            onIdeaCreated={(ideaId) => setCreatedIdeaId(ideaId)}
          />
        </div>
        <div className="flex justify-end gap-3 mt-4">
          <Link
            href="/"
            className="px-4 py-2 border border-border rounded-lg hover:bg-muted transition-colors"
          >
            Cancel
          </Link>
          {createdIdeaId ? (
            <button
              onClick={() => router.push(`/ideas/${createdIdeaId}`)}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
            >
              Continue to Edit →
            </button>
          ) : (
            <button
              onClick={() => router.push("/")}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
            >
              Save as Draft
            </button>
          )}
        </div>
      </main>
    </div>
  );
}
