import { useState, useCallback } from "react";
import type { Message } from "@/types/chat";
import type { ApiError } from "@/services/apiClient";
import { sendChatMessage } from "@/services/chatApi";
import { generateId } from "@/utils/generateId";

const ERROR_MESSAGE = "Something went wrong. Please try again.";

export function useChat(sessionId: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (content: string) => {
      const userMessage: Message = {
        id: generateId(),
        role: "user",
        content,
        createdAt: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setLoading(true);
      setError(null);

      try {
        const reply = await sendChatMessage(sessionId, content);

        const assistantMessage: Message = {
          id: generateId(),
          role: "assistant",
          content: reply,
          createdAt: new Date(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        const apiError = err as ApiError;
        const errorContent = apiError.message || ERROR_MESSAGE;

        const errorMessage: Message = {
          id: generateId(),
          role: "assistant",
          content: errorContent,
          createdAt: new Date(),
        };

        setMessages((prev) => [...prev, errorMessage]);
        setError(errorContent);
      } finally {
        setLoading(false);
      }
    },
    [sessionId],
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, loading, error, sendMessage, clearMessages } as const;
}
