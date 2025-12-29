"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SectionEditor } from "./SectionEditor";
import { api } from "@/lib/api";
import type { IdeaDetail, CoherentAction } from "@/lib/types";

interface IdeaCanvasProps {
  idea: IdeaDetail;
  onUpdate: () => void;
}

/**
 * IdeaCanvas - Structured editing interface for idea concepts.
 *
 * Each section corresponds to a backend Concept and uses the appropriate
 * API endpoint to ensure synchronizations are triggered:
 * - Summary → api.summaries.update() → triggers generate_summary_embedding
 * - Challenge → api.challenges.update() → triggers generate_challenge_embedding
 * - Approach → api.approaches.update() → triggers generate_approach_embedding
 */
export function IdeaCanvas({ idea, onUpdate }: IdeaCanvasProps) {
  /**
   * Update Summary concept.
   * Triggers: summary.updated → generate_summary_embedding, find_similar_ideas
   */
  const handleUpdateSummary = async (content: string) => {
    if (idea.summary) {
      await api.summaries.update(idea.id, content);
    } else {
      await api.summaries.create(idea.id, content);
    }
    onUpdate();
  };

  /**
   * Update Challenge concept.
   * Triggers: challenge.updated → generate_challenge_embedding
   */
  const handleUpdateChallenge = async (content: string) => {
    if (idea.challenge) {
      await api.challenges.update(idea.id, content);
    } else {
      await api.challenges.create(idea.id, content);
    }
    onUpdate();
  };

  /**
   * Update Approach concept.
   * Triggers: approach.updated → generate_approach_embedding
   */
  const handleUpdateApproach = async (content: string) => {
    if (idea.approach) {
      await api.approaches.update(idea.id, content);
    } else {
      await api.approaches.create(idea.id, content);
    }
    onUpdate();
  };

  return (
    <ScrollArea className="h-full">
      <div className="space-y-4 p-4">
        <SectionEditor
          title="Summary"
          content={idea.summary?.content || null}
          placeholder="Describe your idea in a few sentences..."
          onSave={handleUpdateSummary}
        />

        <SectionEditor
          title="Challenge"
          content={idea.challenge?.content || null}
          placeholder="What problem or challenge does this idea address?"
          onSave={handleUpdateChallenge}
          optional
        />

        <SectionEditor
          title="Approach"
          content={idea.approach?.content || null}
          placeholder="What's the guiding policy or approach to address the challenge?"
          onSave={handleUpdateApproach}
          optional
        />

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium">
              Coherent Actions
              {idea.coherent_actions.length === 0 && (
                <span className="ml-2 text-xs text-muted-foreground">
                  (Optional)
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {idea.coherent_actions.length === 0 ? (
              <p className="text-sm italic text-muted-foreground">
                No actions defined yet. Chat with the assistant to suggest some.
              </p>
            ) : (
              <div className="space-y-2">
                {idea.coherent_actions.map((action: CoherentAction) => (
                  <div
                    key={action.id}
                    className="flex items-start gap-3 rounded-md border p-3"
                  >
                    <Badge
                      variant={
                        action.status === "Complete"
                          ? "default"
                          : action.status === "In Progress"
                            ? "secondary"
                            : "outline"
                      }
                      className="mt-0.5 shrink-0"
                    >
                      {action.status}
                    </Badge>
                    <p className="text-sm">{action.content}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </ScrollArea>
  );
}
