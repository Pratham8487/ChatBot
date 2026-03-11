import apiClient from "@/services/apiClient";
import type { ChatApiRequest, ChatApiResponse } from "@/types/chat";

export async function sendChatMessage(
  sessionId: string,
  message: string,
): Promise<string> {
  const payload: ChatApiRequest = {
    session_id: sessionId,
    data: message,
  };

  const response = await apiClient.post<unknown, ChatApiResponse>(
    "/api/chat/?engine=openai",
    payload,
  );

  if (!response.isSuccess || !response.data) {
    throw new Error(response.error ?? "Failed to get response");
  }

  return response.data.response;
}
