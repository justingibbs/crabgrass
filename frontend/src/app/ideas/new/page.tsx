"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useCopilotChat } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { Header } from "@/components/layout";
import { Button } from "@/components/ui/button";

export default function NewIdeaPage() {
  const router = useRouter();
  const [savedIdeaId, setSavedIdeaId] = useState<string | null>(null);

  const handleSaveAsDraft = () => {
    if (savedIdeaId) {
      router.push("/");
    } else {
      router.push("/");
    }
  };

  const handleContinueToEdit = () => {
    if (savedIdeaId) {
      router.push(`/ideas/${savedIdeaId}`);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Header title="New Idea" showBack />

      <div className="flex flex-1 flex-col">
        <div className="flex-1">
          <CopilotChat
            className="h-[calc(100vh-120px)]"
            instructions="Help the user capture and structure their idea. Start by asking what's on their mind. Guide them toward articulating a clear summary, and optionally a challenge, approach, and coherent actions. Be conversational but concise."
            labels={{
              title: "Idea Assistant",
              initial:
                "Hi! I'm here to help you capture and structure your idea. What's on your mind?",
              placeholder: "Describe your idea or respond to the assistant...",
            }}
            onSubmitMessage={(message) => {
              console.log("Message submitted:", message);
            }}
          />
        </div>

        <div className="border-t bg-background p-4">
          <div className="container flex justify-end gap-3">
            <Button variant="outline" onClick={handleSaveAsDraft}>
              Save as Draft
            </Button>
            {savedIdeaId && (
              <Button onClick={handleContinueToEdit}>Continue to Edit</Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
