import { client } from "@repo/sdk";

// Store the current token in a module-level variable
let currentToken: string | null = null;

// 浏览器可访问的 API baseUrl（环境变量驱动；默认本地开发）
// 部署时通过 NEXT_PUBLIC_API_BASE_URL 指向真实后端，避免 SDK 生成物中的硬编码 localhost
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/**
 * Configure the SDK client with authentication token
 */
export function configureApiClient(token: string | null) {
  currentToken = token;

  if (token) {
    client.setConfig({
      baseUrl: API_BASE_URL,
      auth: () => token,
    });
  } else {
    client.setConfig({
      baseUrl: API_BASE_URL,
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
 * Get the configured API base URL
 */
export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

/**
 * Get the configured API client
 */
export { client };
