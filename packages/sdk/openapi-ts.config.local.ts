import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: 'http://localhost:8000/openapi.json',
  output: {
    path: './src/api',
    module: {
        extension: '.js',           // ← 添加这一行
      },
  },
  
  plugins: [
      '@hey-api/typescript',
      '@hey-api/sdk',
      'zod',
      '@hey-api/client-fetch',
      '@tanstack/react-query',          // ← can often be just the string
    ],
});