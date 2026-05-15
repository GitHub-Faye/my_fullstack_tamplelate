import { client } from "@repo/sdk";

// Store the current token in a module-level variable
let currentToken: string | null = null;

/**
 * Configure the SDK client with authentication token
 */
export function configureApiClient(token: string | null) {
  currentToken = token;
  
  if (token) {
    client.setConfig({
      auth: () => token,
    });
  } else {
    client.setConfig({
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
