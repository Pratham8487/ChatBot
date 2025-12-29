const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function sendMessage(message: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/chat/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    throw new Error("Failed to fetch AI response");
  }

  const data = await response.json();
  return data.reply;
}
