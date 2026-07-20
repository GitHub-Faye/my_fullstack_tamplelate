# 03 — 后端 API：扩展筛选参数

**What to build:** 在 GET `/tasks` 端点添加 `task_type`, `engineer_id` 查询参数支持。

**Blocked by:** #02 — Schema 扩展完成后

**Status:** ready-for-agent

- [ ] 在 router 的 `GET /tasks` 添加 `task_type: str | None`, `engineer_id: str | None` 参数
- [ ] 更新 repository 筛选逻辑支持这两个新参数
- [ ] 更新 OpenAPI 文档（自动生成）
- [ ] 确保 SDK 类型重新生成