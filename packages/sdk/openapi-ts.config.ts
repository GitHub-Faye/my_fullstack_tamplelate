import { defineConfig } from "@hey-api/openapi-ts";

/**
 * SDK 生成配置
 *
 * input 指向仓库内的 openapi.json 快照，保证 CI / 新接入方
 * 在【未启动后端】时也能离线生成 SDK。
 *
 * 后端接口变更后，需刷新快照再重新生成：
 *   pnpm generate:live   # 启动后端后：拉取 /openapi.json 覆盖快照 + 重新生成
 *   pnpm generate        # 用仓库内快照重新生成（离线可用）
 */
export default defineConfig({
  input: "./openapi.json",
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
