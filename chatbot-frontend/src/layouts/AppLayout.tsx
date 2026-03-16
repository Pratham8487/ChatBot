import { useState } from "react";
import type { ChatSession } from "@/types/chat";
import { useTheme } from "@/hooks/useTheme";
import { useChatSession } from "@/hooks/useChatSession";
import { useChat } from "@/hooks/useChat";
import Sidebar from "@/components/sidebar/Sidebar";
import ChatContainer from "@/components/chat/ChatContainer";

const MOCK_SESSIONS: ChatSession[] = [
  { id: "1", title: "Current Chat" },
];

function AppLayout() {
  const { theme, toggleTheme } = useTheme();
  const { sessionId, resetSession } = useChatSession();
  const { messages, loading, sendMessage, clearMessages } = useChat(sessionId);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState(MOCK_SESSIONS[0].id);

  function handleNewChat() {
    resetSession();
    clearMessages();
    setActiveSessionId("");
  }

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900">
      <Sidebar
        sessions={MOCK_SESSIONS}
        activeSessionId={activeSessionId}
        isOpen={sidebarOpen}
        theme={theme}
        onNewChat={handleNewChat}
        onSelectSession={setActiveSessionId}
        onToggleTheme={toggleTheme}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex flex-col flex-1 min-w-0">
        {/* Mobile header */}
        <header className="flex items-center px-4 py-3 border-b border-gray-200 dark:border-gray-800 md:hidden">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open sidebar"
            className="flex items-center justify-center w-9 h-9 rounded-lg
              text-gray-500 dark:text-gray-400
              hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
              className="w-5 h-5"
            >
              <line x1={3} y1={12} x2={21} y2={12} />
              <line x1={3} y1={6} x2={21} y2={6} />
              <line x1={3} y1={18} x2={21} y2={18} />
            </svg>
          </button>
          <span className="ml-3 text-sm font-semibold text-gray-800 dark:text-gray-200">
            ChatBot
          </span>
        </header>

        <ChatContainer
          messages={messages}
          loading={loading}
          onSendMessage={sendMessage}
        />
      </div>
    </div>
  );
}

export default AppLayout;
