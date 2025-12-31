"use client";

import { useState, useCallback, useRef } from "react";
import type { Suggestion } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export interface IdeaContext {
  idea_id: string | null;
  title: string | null;
  summary: string | null;
  challenge: string | null;
  approach: string | null;
  coherent_actions: string[];
  stage: string;
}

interface UseAgentChatOptions {
  sessionId?: string | null;
  ideaId?: string | null;
  onIdeaCreated?: (ideaId: string) => void;
  onContextUpdate?: (context: IdeaContext) => void;
  onSuggestion?: (suggestion: Suggestion) => void;
}

export function useAgentChat(options: UseAgentChatOptions = {}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(options.sessionId || null);
  const [context, setContext] = useState<IdeaContext | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: content.trim(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${API_BASE}/api/agent/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: content.trim(),
          session_id: sessionId,
          idea_id: options.ideaId,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }

      // Get session ID from header
      const newSessionId = response.headers.get("X-Session-Id");
      if (newSessionId && !sessionId) {
        setSessionId(newSessionId);
      }

      // Process SSE stream
      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let assistantMessageId: string | null = null;
      let assistantContent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;

          try {
            const data = JSON.parse(line.slice(6));

            switch (data.type) {
              case "TEXT_MESSAGE_START":
                assistantMessageId = data.messageId;
                assistantContent = "";
                // Add placeholder message
                setMessages((prev) => [
                  ...prev,
                  { id: assistantMessageId!, role: "assistant", content: "" },
                ]);
                break;

              case "TEXT_MESSAGE_CONTENT":
                if (assistantMessageId && data.delta) {
                  assistantContent += data.delta;
                  // Update message content
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMessageId
                        ? { ...m, content: assistantContent }
                        : m
                    )
                  );
                }
                break;

              case "STATE_SNAPSHOT":
                if (data.snapshot) {
                  setContext(data.snapshot);
                  options.onContextUpdate?.(data.snapshot);

                  // Check if idea was created
                  if (data.snapshot.idea_id && options.onIdeaCreated) {
                    options.onIdeaCreated(data.snapshot.idea_id);
                  }
                }
                break;

              case "TOOL_CALL_START":
                // Could show tool usage indicator
                break;

              case "TOOL_CALL_RESULT":
                // Tool result received
                try {
                  const result = JSON.parse(data.content);
                  if (result.idea_id && options.onIdeaCreated) {
                    options.onIdeaCreated(result.idea_id);
                  }
                } catch {
                  // Ignore parse errors
                }
                break;

              case "CUSTOM":
                // Handle custom events like SUGGESTION
                if (data.name === "SUGGESTION" && data.value && options.onSuggestion) {
                  const suggestion: Suggestion = {
                    suggestion_id: data.value.suggestion_id,
                    field: data.value.field,
                    content: data.value.content,
                    reason: data.value.reason || "",
                  };
                  options.onSuggestion(suggestion);
                }
                break;
            }
          } catch {
            // Ignore parse errors for incomplete JSON
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        // Request was cancelled
        return;
      }
      const errorMessage = err instanceof Error ? err.message : "Failed to send message";
      setError(errorMessage);
      // Add error message
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: `Error: ${errorMessage}`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, sessionId, options]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setContext(null);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sessionId,
    context,
    sendMessage,
    clearMessages,
  };
}
