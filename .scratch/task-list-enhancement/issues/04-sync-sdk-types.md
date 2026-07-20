# 04 — 前端 SDK 类型同步

**What to build:** 在 `packages/sdk` 中同步更新 TypeScript 类型定义，匹配后端 `TaskPublic` 新增字段。

**Blocked by:** #02 — 后端 Schema 更新完成后

**Status:** ready-for-agent

- [ ] 运行 OpenAPI 代码生成（`pnpm gen:sdk` 或等效命令）
- [ ] 若无自动生成，手动更新 `TaskPublic` 类型添加：`expected_online_time`, `T_reported_complete_time`, `progress`, `pm_name`, `engineer_name`
- [ ] 验证类型编译通过

**Implementation Note:**
- Check if there's an OpenAPI spec generation script (e.g., in `apps/api/Makefile` or `package.json`)
- The SDK is at `packages/sdk/src/index.ts` — generated types may be in `packages/sdk/src/gen/`