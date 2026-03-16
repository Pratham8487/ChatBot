import type { Message } from "@/types/chat";
import MessageBubble from "@/components/chat/MessageBubble";

interface MessageListProps {
  messages: Message[];
}

function MessageList({ messages }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-4">
        <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-200 mb-2">
          How can I help you today?
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Start a conversation by typing a message below.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
    </div>
  );
}

export default MessageList;
