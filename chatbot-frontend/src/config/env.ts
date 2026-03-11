interface EnvConfig {
  readonly apiBaseUrl: string;
  readonly isDev: boolean;
  readonly isProd: boolean;
  readonly mode: string;
}

function getEnvVar(key: string): string {
  const value = import.meta.env[key];
  if (!value || typeof value !== "string" || value.trim() === "") {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value.trim();
}

const env: EnvConfig = {
  apiBaseUrl: getEnvVar("VITE_API_BASE_URL"),
  isDev: import.meta.env.DEV === true,
  isProd: import.meta.env.PROD === true,
  mode: import.meta.env.MODE ?? "development",
};

export default env;
