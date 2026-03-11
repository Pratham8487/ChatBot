export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: Date;
}

export interface ChatSession {
  id: string;
  title: string;
}

export interface ChatApiRequest {
  session_id: string;
  data: string;
}

export interface ChatApiResponseData {
  engine: string;
  stage: string;
  duration: number;
  response: string;
  lead: {
    qualified: boolean;
    intent_level: string;
    email: string;
    phone: string;
  };
}

export interface ChatApiResponse {
  isSuccess: boolean;
  data: ChatApiResponseData | null;
  error: string | null;
}
