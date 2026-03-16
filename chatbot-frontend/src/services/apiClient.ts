import axios, { type AxiosError, type AxiosResponse } from "axios";
import env from "@/config/env";

interface ApiError {
  message: string;
  status: number;
  data: unknown;
}

function normalizeError(error: AxiosError): ApiError {
  const status = error.response?.status ?? 0;
  const data = error.response?.data ?? null;

  let message = "An unexpected error occurred";
  if (error.code === "ECONNABORTED") {
    message = "Request timed out";
  } else if (!error.response) {
    message = "Network error — unable to reach server";
  } else if (typeof data === "object" && data !== null && "detail" in data) {
    message = String((data as Record<string, unknown>).detail);
  }

  return { message, status, data };
}

const apiClient = axios.create({
  baseURL: env.apiBaseUrl,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

apiClient.interceptors.response.use(
  (response: AxiosResponse) => response.data,
  (error: AxiosError) => Promise.reject(normalizeError(error)),
);

export type { ApiError };
export default apiClient;
