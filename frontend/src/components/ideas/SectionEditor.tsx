"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

interface SectionEditorProps {
  title: string;
  content: string | null;
  placeholder: string;
  onSave: (content: string) => Promise<void>;
  optional?: boolean;
}

export function SectionEditor({
  title,
  content,
  placeholder,
  onSave,
  optional = false,
}: SectionEditorProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(content || "");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setEditValue(content || "");
  }, [content]);

  const handleSave = async () => {
    try {
      setIsSaving(true);
      await onSave(editValue);
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

  const isEmpty = !content || content.trim() === "";

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-medium">
            {title}
            {optional && isEmpty && (
              <span className="ml-2 text-xs text-muted-foreground">
                (Optional)
              </span>
            )}
          </CardTitle>
          {!isEditing && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsEditing(true)}
            >
              {isEmpty ? "Add" : "Edit"}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {isEditing ? (
          <div className="space-y-3">
            <Textarea
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              placeholder={placeholder}
              className="min-h-[100px] resize-none"
              autoFocus
            />
            <div className="flex justify-end gap-2">
              <Button variant="ghost" size="sm" onClick={handleCancel}>
                Cancel
              </Button>
              <Button size="sm" onClick={handleSave} disabled={isSaving}>
                {isSaving ? "Saving..." : "Save"}
              </Button>
            </div>
          </div>
        ) : isEmpty ? (
          <p className="text-sm italic text-muted-foreground">{placeholder}</p>
        ) : (
          <p className="whitespace-pre-wrap text-sm">{content}</p>
        )}
      </CardContent>
    </Card>
  );
}
