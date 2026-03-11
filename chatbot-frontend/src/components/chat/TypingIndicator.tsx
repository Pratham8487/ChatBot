function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="flex items-center gap-1 px-4 py-3 rounded-2xl rounded-bl-md
        bg-gray-100 dark:bg-gray-800"
      >
        <span className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce [animation-delay:0ms]" />
        <span className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce [animation-delay:150ms]" />
        <span className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce [animation-delay:300ms]" />
      </div>
    </div>
  );
}

export default TypingIndicator;
