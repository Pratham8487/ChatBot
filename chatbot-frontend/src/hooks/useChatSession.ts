import { useState, useCallback } from "react";
import { generateId } from "@/utils/generateId";

const SESSION_KEY = "chat_session_id";

function getOrCreateSessionId(): string {
  const stored = localStorage.getItem(SESSION_KEY);
  if (stored) return stored;

  const id = generateId();
  localStorage.setItem(SESSION_KEY, id);
  return id;
}

export function useChatSession() {
  const [sessionId, setSessionId] = useState(getOrCreateSessionId);

  const resetSession = useCallback(() => {
    const id = generateId();
    localStorage.setItem(SESSION_KEY, id);
    setSessionId(id);
  }, []);

  return { sessionId, resetSession } as const;
}
