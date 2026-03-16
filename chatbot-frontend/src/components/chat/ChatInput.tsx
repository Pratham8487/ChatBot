import { useState, useRef, type FormEvent, type KeyboardEvent } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const trimmed = value.trim();

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    textareaRef.current?.focus();
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  return (
    <div className="border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 px-4 py-3">
      <form
        onSubmit={handleSubmit}
        className="mx-auto flex items-end gap-2 max-w-3xl"
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none rounded-2xl border border-gray-300 dark:border-gray-700
            bg-gray-50 dark:bg-gray-800
            text-gray-800 dark:text-gray-200
            placeholder-gray-400 dark:placeholder-gray-500
            px-4 py-3 text-sm leading-relaxed
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
            disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!trimmed || disabled}
          className="flex items-center justify-center w-10 h-10 rounded-full
            bg-blue-600 text-white
            hover:bg-blue-700
            disabled:opacity-40 disabled:cursor-not-allowed
            shrink-0"
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
            <line x1={22} y1={2} x2={11} y2={13} />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </form>
    </div>
  );
}

export default ChatInput;
