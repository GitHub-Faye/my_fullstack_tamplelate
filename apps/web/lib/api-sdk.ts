import { client } from "@repo/sdk";

// Store the current token in a module-level variable
let currentToken: string | null = null;

// 初始化 API baseUrl
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
client.setConfig({ baseUrl: API_URL });

/**
 * Configure the SDK client with authentication token
 */
export function configureApiClient(token: string | null) {
  currentToken = token;

  if (token) {
    client.setConfig({
      baseUrl: API_URL,
      auth: () => token,
    });
  } else {
    client.setConfig({
      baseUrl: API_URL,
      auth: undefined,
    });
  }
}

/**
 * Get the current auth token
 */
export function getAuthToken(): string | null {
  return currentToken;
}

/**
 * Get the configured API client
 */
export { client };
