import type { ChatSession } from "@/types/chat";

interface SidebarItemProps {
  session: ChatSession;
  isActive: boolean;
  onClick: (id: string) => void;
}

function SidebarItem({ session, isActive, onClick }: SidebarItemProps) {
  return (
    <button
      type="button"
      onClick={() => onClick(session.id)}
      className={`flex items-center w-full px-4 py-2.5 rounded-xl text-sm text-left
        truncate transition-colors
        ${
          isActive
            ? "bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white font-medium"
            : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700/50"
        }`}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        className="w-4 h-4 mr-3 shrink-0"
      >
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
      <span className="truncate">{session.title}</span>
    </button>
  );
}

export default SidebarItem;
