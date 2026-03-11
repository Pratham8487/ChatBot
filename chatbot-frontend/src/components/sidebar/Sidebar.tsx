import type { ChatSession } from "@/types/chat";
import NewChatButton from "@/components/sidebar/NewChatButton";
import SidebarItem from "@/components/sidebar/SidebarItem";
import ThemeToggle from "@/components/common/ThemeToggle";

interface SidebarProps {
  sessions: ChatSession[];
  activeSessionId: string;
  isOpen: boolean;
  theme: "light" | "dark";
  onNewChat: () => void;
  onSelectSession: (id: string) => void;
  onToggleTheme: () => void;
  onClose: () => void;
}

function Sidebar({
  sessions,
  activeSessionId,
  isOpen,
  theme,
  onNewChat,
  onSelectSession,
  onToggleTheme,
  onClose,
}: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/30 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed md:static z-30 inset-y-0 left-0
          flex flex-col w-64 h-screen
          bg-white dark:bg-gray-900
          border-r border-gray-200 dark:border-gray-800
          transform transition-transform duration-200 ease-in-out
          ${isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0 md:hidden"}
          md:flex`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-4">
          <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">
            ChatBot
          </span>
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        </div>

        {/* New Chat */}
        <div className="px-3 pb-3">
          <NewChatButton onClick={onNewChat} />
        </div>

        {/* Session list */}
        <nav className="flex-1 overflow-y-auto px-3 space-y-1">
          {sessions.map((session) => (
            <SidebarItem
              key={session.id}
              session={session}
              isActive={session.id === activeSessionId}
              onClick={onSelectSession}
            />
          ))}
        </nav>
      </aside>
    </>
  );
}

export default Sidebar;
