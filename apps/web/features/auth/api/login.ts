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
  const formData: BodyLoginAccessTokenV1LoginAccessTokenPost = {
    username: credentials.email,
    password: credentials.password,
    grant_type: 'password',
    scope: '',
    client_id: null,
    client_secret: null,
  };

  const response = await client.post({
    url: '/v1/login/access-token',
    body: formData,
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });

  if (response.error) {
    throw new Error('Login failed');
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
