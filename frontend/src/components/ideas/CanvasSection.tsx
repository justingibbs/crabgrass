"use client";

import { useState, useRef, useEffect } from "react";
import { Pencil, Check, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface CanvasSectionProps {
  title: string;
  content: string | null;
  placeholder: string;
  onSave: (content: string) => Promise<void>;
  isEditable?: boolean;
}

export function CanvasSection({
  title,
  content,
  placeholder,
  onSave,
  isEditable = true,
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
    </div>
  );
}
