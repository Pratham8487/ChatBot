import { useEffect, useRef } from "react";
import type { Message } from "@/types/chat";
import MessageList from "@/components/chat/MessageList";
import ChatInput from "@/components/chat/ChatInput";
import TypingIndicator from "@/components/chat/TypingIndicator";

interface ChatContainerProps {
  messages: Message[];
  loading: boolean;
  onSendMessage: (message: string) => void;
}

function ChatContainer({ messages, loading, onSendMessage }: ChatContainerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  }, [messages.length, loading]);

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-3xl">
          <MessageList messages={messages} />
          {loading && (
            <div className="mt-4">
              <TypingIndicator />
            </div>
          )}
        </div>
      </div>

      <ChatInput onSend={onSendMessage} disabled={loading} />
    </div>
  );
}

export default ChatContainer;
