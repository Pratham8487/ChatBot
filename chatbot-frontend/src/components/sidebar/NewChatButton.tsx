interface NewChatButtonProps {
  onClick: () => void;
}

function NewChatButton({ onClick }: NewChatButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex items-center gap-2 w-full px-4 py-2.5 rounded-xl
        text-sm font-medium
        text-gray-700 dark:text-gray-200
        bg-gray-100 dark:bg-gray-700
        hover:bg-gray-200 dark:hover:bg-gray-600"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        className="w-4 h-4"
      >
        <line x1={12} y1={5} x2={12} y2={19} />
        <line x1={5} y1={12} x2={19} y2={12} />
      </svg>
      New Chat
    </button>
  );
}

export default NewChatButton;
