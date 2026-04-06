// src/hey-api.config.ts
import type { CreateClientConfig } from '@hey-api/client-fetch';   // 注意：根据你实际生成的路径调整

// 如果你用了 @hey-api/client-next，则改成：
// import type { CreateClientConfig } from '@hey-api/client-next';

export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  // 这里设置你的后端真实地址（强烈推荐用环境变量）
  baseUrl: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000', // 改成你的后端端口
  
  // 可选：全局 headers、credentials 等
  // credentials: 'include',
  // headers: {
  //   'Content-Type': 'application/json',
  // },
});