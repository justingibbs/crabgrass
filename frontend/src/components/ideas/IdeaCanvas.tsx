"use client";

import { useState } from "react";
import { Plus, Trash2, Check, Circle, PlayCircle } from "lucide-react";
import type { IdeaDetail, CoherentAction } from "@/lib/types";
import { api } from "@/lib/api";
import { CanvasSection } from "./CanvasSection";
import { cn } from "@/lib/utils";

interface IdeaCanvasProps {
  idea: IdeaDetail;
  onUpdate: () => void;
  className?: string;
}

export function IdeaCanvas({ idea, onUpdate, className }: IdeaCanvasProps) {
  const [newActionContent, setNewActionContent] = useState("");
  const [isAddingAction, setIsAddingAction] = useState(false);

  const handleSaveSummary = async (content: string) => {
    if (idea.summary) {
      await api.summaries.update(idea.id, content);
    } else {
      await api.summaries.create(idea.id, content);
    }
    onUpdate();
  };

  const handleSaveChallenge = async (content: string) => {
    if (idea.challenge) {
      await api.challenges.update(idea.id, content);
    } else {
      await api.challenges.create(idea.id, content);
    }
    onUpdate();
  };

  const handleSaveApproach = async (content: string) => {
    if (idea.approach) {
      await api.approaches.update(idea.id, content);
    } else {
      await api.approaches.create(idea.id, content);
    }
    onUpdate();
  };

  const handleAddAction = async () => {
    if (!newActionContent.trim()) return;
    setIsAddingAction(true);
    try {
      await api.actions.create(idea.id, newActionContent.trim());
      setNewActionContent("");
      onUpdate();
    } finally {
      setIsAddingAction(false);
    }
  };

  const handleUpdateActionStatus = async (
    action: CoherentAction,
    newStatus: CoherentAction["status"]
  ) => {
    if (newStatus === "Complete") {
      await api.actions.complete(idea.id, action.id);
    } else {
      await api.actions.update(idea.id, action.id, { status: newStatus });
    }
    onUpdate();
  };

  const handleDeleteAction = async (actionId: string) => {
    await api.actions.delete(idea.id, actionId);
    onUpdate();
  };

  return (
    <div className={cn("space-y-4 overflow-y-auto", className)}>
      <CanvasSection
        title="Summary"
        content={idea.summary?.content || null}
        placeholder="What's the core idea? Describe it in a few sentences..."
        onSave={handleSaveSummary}
      />

      <CanvasSection
        title="Challenge"
        content={idea.challenge?.content || null}
        placeholder="What problem does this solve? What opportunity does it address?"
        onSave={handleSaveChallenge}
      />

      <CanvasSection
        title="Approach"
        content={idea.approach?.content || null}
        placeholder="How would you tackle this? What's your proposed solution?"
        onSave={handleSaveApproach}
      />

      {/* Coherent Actions - special handling for list */}
      <div className="border border-border rounded-lg p-4">
        <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wide mb-3">
          Coherent Actions
        </h3>

        {idea.coherent_actions.length === 0 && (
          <p className="text-muted-foreground italic mb-3">
            No actions yet. Add steps to bring this idea to life.
          </p>
        )}

        <ul className="space-y-2 mb-3">
          {idea.coherent_actions.map((action) => (
            <li
              key={action.id}
              className="flex items-start gap-2 group"
            >
              <button
                onClick={() => {
                  const nextStatus: CoherentAction["status"] =
                    action.status === "Pending"
                      ? "In Progress"
                      : action.status === "In Progress"
                      ? "Complete"
                      : "Pending";
                  handleUpdateActionStatus(action, nextStatus);
                }}
                className="mt-0.5 flex-shrink-0"
                title={`Status: ${action.status}. Click to change.`}
              >
                {action.status === "Complete" ? (
                  <Check className="w-5 h-5 text-green-600" />
                ) : action.status === "In Progress" ? (
                  <PlayCircle className="w-5 h-5 text-blue-600" />
                ) : (
                  <Circle className="w-5 h-5 text-muted-foreground" />
                )}
              </button>
              <span
                className={cn(
                  "flex-1",
                  action.status === "Complete" && "line-through text-muted-foreground"
                )}
              >
                {action.content}
              </span>
              <button
                onClick={() => handleDeleteAction(action.id)}
                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded transition-all text-red-600"
                aria-label="Delete action"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </li>
          ))}
        </ul>

        <div className="flex gap-2">
          <input
            type="text"
            value={newActionContent}
            onChange={(e) => setNewActionContent(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAddAction()}
            placeholder="Add a new action..."
            disabled={isAddingAction}
            className="flex-1 px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          <button
            onClick={handleAddAction}
            disabled={isAddingAction || !newActionContent.trim()}
            className="px-3 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
