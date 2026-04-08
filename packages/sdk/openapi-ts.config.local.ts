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
    '@hey-api/typescript',       // 类型
    '@hey-api/sdk',              // 生成 services / sdk
    '@tanstack/react-query',

    // 推荐替换成 Next.js 专用 client（更适合 Next.js）
    {
      name: '@hey-api/client-fetch',   // 或者直接用内置的 fetch（新版本已集成）
      // runtimeConfigPath: './src/hey-api.config.ts',   // ← 关键！指向运行时配置文件
    },
    
    // 如果你想用更专用的 Next.js client（推荐尝试）
    // { name: '@hey-api/client-next', runtimeConfigPath: './src/hey-api.config.ts' },
  ],
});