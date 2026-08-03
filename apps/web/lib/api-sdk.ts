import { client } from "@repo/sdk";

// Store the current token in a module-level variable
let currentToken: string | null = null;

// 初始化 API baseUrl
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
client.setConfig({ baseUrl: API_URL });

// 防止拦截器里重复触发 logout（避免循环）
let handlingUnauthorized = false;

/**
 * 全局 401 处理：token 过期/无效时清除本地认证状态，
 * 使 dashboard layout 检测到未认证后跳转到 /login。
 *
 * 通过 setTimeout 延迟执行，避免在请求错误抛出的同步栈里直接改 store。
 */
client.interceptors.error.use((error, response) => {
  const status = (response as Response | undefined)?.status;
  if (status === 401 && !handlingUnauthorized) {
    handlingUnauthorized = true;
    // 动态 import，避免循环依赖（api-sdk.ts 被 auth store 依赖）
    setTimeout(async () => {
      try {
        const { useAuthStore } = await import("@/features/user/stores/auth");
        useAuthStore.getState().logout();
      } finally {
        handlingUnauthorized = false;
      }
    }, 0);
  }
  return error;
});

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
