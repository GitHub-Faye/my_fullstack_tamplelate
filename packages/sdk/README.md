# @repo/sdk

Auto-generated API SDK for the FastAPI backend.

## Overview

This package is automatically generated from the FastAPI OpenAPI specification using `@hey-api/openapi-ts`.

## Installation

```bash
pnpm add @repo/sdk
```

## Usage

### Basic Usage

```typescript
import { client } from '@repo/sdk';

// Configure the client
client.setConfig({
  baseUrl: 'http://localhost:8000',
});

// Make API calls
const response = await client.get({
  url: '/v1/users/users/me',
});

if (response.error) {
  console.error('Error:', response.error);
} else {
  console.log('User:', response.data);
}
```

### With Authentication

```typescript
import { client } from '@repo/sdk';

// Add auth token interceptor
client.interceptors.request.use((request) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    request.headers.set('Authorization', `Bearer ${token}`);
  }
  return request;
});
```

### Using Types

```typescript
import type { UserPublic, Token, ItemCreate } from '@repo/sdk';

// Use types in your components
interface Props {
  user: UserPublic;
}

// Create item
const newItem: ItemCreate = {
  title: 'My Item',
  description: 'Description',
};
```

## Regenerating the SDK

When the API changes, regenerate the SDK:

```bash
cd packages/sdk
pnpm generate:local
```

This will:
1. Fetch the OpenAPI spec from `http://localhost:8000/openapi.json`
2. Generate TypeScript types and client
3. Format with Prettier
4. Lint with ESLint

## API Endpoints

The SDK includes all endpoints from the FastAPI backend:

- **Login**: `/v1/login/access-token`, `/v1/login/test-token`
- **Users**: `/v1/users/users/*`
- **Items**: `/v1/items/items/*`

## License

MIT
