import type { Message } from "@/types/chat";

interface MessageBubbleProps {
  message: Message;
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"} animate-fade-in`}
    >
      <div
        className={`max-w-[70%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm
          ${
            isUser
              ? "bg-blue-600 text-white rounded-br-md"
              : "bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-bl-md"
          }`}
      >
        {message.content}
      </div>
    </div>
  );
}

export default MessageBubble;
