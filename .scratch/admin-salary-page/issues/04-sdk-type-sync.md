# 04 — SDK 类型同步

**What to build:** 重新生成 SDK 类型，使前端能安全地使用 `EngineerSalarySummary`、`PMSalarySummary` 等新 schema 和 `month` query 参数。由 `openapi-ts` 自动生成。

**Blocked by:** #01 — 后端 Schema + Service

**Status:** ready-for-agent

- [ ] 运行 `openapi-ts` 生成 SDK 类型
- [ ] SDK 中新增 `EngineerSalarySummary`、`PMSalarySummary` 类型可用
- [ ] 前端类型安全，无 TS 编译错误