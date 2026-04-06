// Login API using @repo/sdk
import { client, type BodyLoginAccessTokenV1LoginAccessTokenPost } from '@repo/sdk';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export async function login(credentials: LoginCredentials): Promise<LoginResponse> {
  const formData = new URLSearchParams();
  formData.append('username', credentials.email);
  formData.append('password', credentials.password);
  formData.append('grant_type', 'password');
  formData.append('scope', '');

  const response = await client.post({
    url: '/v1/login/access-token',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString(),
  });

  if (response.error) {
    // Try to get more detailed error information
    const errorDetails = (response.error as any)?.data?.detail ||
                       (response.error as any)?.data ||
                       response.error;
    console.error('Login error details:', errorDetails);
    throw new Error('Login failed: ' + JSON.stringify(errorDetails));
  }

  return response.data as LoginResponse;
}

export async function getCurrentUser() {
  const response = await client.get({
    url: '/v1/users/users/me',
  });

  if (response.error) {
    throw new Error('Failed to get current user');
  }

  return response.data;
}
