import { defineConfig } from "@hey-api/openapi-ts";

/**
 * 基础 SDK 生成配置
 *
 * 用途：作为 generate 的默认基线配置。当 openapi-ts.config.local.ts
 * 不存在或未通过 -f 显式指定时，pnpm generate 会使用本文件。
 *
 * 注意：input 写死 http://localhost:8000/openapi.json 仅为开发默认值；
 * CI/其他环境请复制本文件为 openapi-ts.config.<env>.ts 并修改 input。
 */
export default defineConfig({
  input: "http://localhost:8000/openapi.json",
  output: {
    path: "./src/api",
    module: {
      extension: ".js",
    },
  },
  plugins: [
    "@hey-api/client-fetch",
    "@hey-api/typescript",
    "zod",
    "@hey-api/sdk",
    "@tanstack/react-query",
  ],
});
