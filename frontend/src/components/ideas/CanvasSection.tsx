"use client";

import { useState, useRef, useEffect } from "react";
import { Pencil, Check, X, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Suggestion } from "@/lib/types";

interface CanvasSectionProps {
  title: string;
  content: string | null;
  placeholder: string;
  onSave: (content: string) => Promise<void>;
  isEditable?: boolean;
  suggestion?: Suggestion | null;
  onAcceptSuggestion?: () => void;
  onRejectSuggestion?: () => void;
}

export function CanvasSection({
  title,
  content,
  placeholder,
  onSave,
  isEditable = true,
  suggestion,
  onAcceptSuggestion,
  onRejectSuggestion,
}: CanvasSectionProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(content || "");
  const [isSaving, setIsSaving] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setEditValue(content || "");
  }, [content]);

  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.setSelectionRange(
        textareaRef.current.value.length,
        textareaRef.current.value.length
      );
    }
  }, [isEditing]);

  const handleSave = async () => {
    if (editValue.trim() === (content || "").trim()) {
      setIsEditing(false);
      return;
    }

    setIsSaving(true);
    try {
      await onSave(editValue.trim());
      setIsEditing(false);
    } catch (error) {
      console.error("Failed to save:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditValue(content || "");
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      handleCancel();
    } else if (e.key === "Enter" && e.metaKey) {
      handleSave();
    }
  };

  return (
    <div className="border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
          {title}
        </h3>
        {isEditable && !isEditing && (
          <button
            onClick={() => setIsEditing(true)}
            className="p-1 hover:bg-muted rounded transition-colors"
            aria-label={`Edit ${title}`}
          >
            <Pencil className="w-4 h-4 text-muted-foreground" />
          </button>
        )}
        {isEditing && (
          <div className="flex items-center gap-1">
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="p-1 hover:bg-green-100 rounded transition-colors text-green-600"
              aria-label="Save"
            >
              <Check className="w-4 h-4" />
            </button>
            <button
              onClick={handleCancel}
              disabled={isSaving}
              className="p-1 hover:bg-red-100 rounded transition-colors text-red-600"
              aria-label="Cancel"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {isEditing ? (
        <textarea
          ref={textareaRef}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isSaving}
          className={cn(
            "w-full min-h-[100px] p-2 border border-border rounded resize-none",
            "focus:outline-none focus:ring-2 focus:ring-primary/50",
            "disabled:opacity-50"
          )}
        />
      ) : (
        <p
          className={cn(
            "whitespace-pre-wrap",
            content ? "text-foreground" : "text-muted-foreground italic"
          )}
        >
          {content || placeholder}
        </p>
      )}

      {isEditing && (
        <p className="text-xs text-muted-foreground mt-2">
          Press Cmd+Enter to save, Esc to cancel
        </p>
      )}

      {/* Suggestion display with Accept/Reject */}
      {suggestion && !isEditing && (
        <div
          className="mt-3 border-2 border-yellow-300 bg-yellow-50 rounded-lg p-3"
          data-testid="suggestion-box"
        >
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-yellow-600" />
            <span className="text-sm font-medium text-yellow-800">
              Suggested by AI
            </span>
          </div>
          <p className="text-sm whitespace-pre-wrap mb-2">{suggestion.content}</p>
          {suggestion.reason && (
            <p className="text-xs text-yellow-700 mb-3">
              Reason: {suggestion.reason}
            </p>
          )}
          <div className="flex gap-2">
            <button
              onClick={onAcceptSuggestion}
              className="flex items-center gap-1 px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
              data-testid="accept-suggestion"
            >
              <Check className="w-3 h-3" />
              Accept
            </button>
            <button
              onClick={onRejectSuggestion}
              className="flex items-center gap-1 px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-100 transition-colors"
              data-testid="reject-suggestion"
            >
              <X className="w-3 h-3" />
              Reject
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
