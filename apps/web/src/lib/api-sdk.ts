// API SDK Client
// This is a wrapper around @repo/sdk to configure the client for the web app

import { client } from '@repo/sdk';

// Configure the API client
client.setConfig({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
});

// Add auth token interceptor
client.interceptors.request.use((request) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  if (token) {
    request.headers.set('Authorization', `Bearer ${token}`);
  }
  return request;
});

export { client };
export * from '@repo/sdk';
