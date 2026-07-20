# 01 — 后端迁移：新增 expected_online_time 和 T_reported_complete_time 字段

**What to build:** 在 Task 数据库表新增 `expected_online_time` 和 `T_reported_complete_time` 两个字段，生成 Alembic 迁移文件。

**Blocked by:** None — 可以立即开始

**Status:** ready-for-agent

- [ ] 创建 Alembic migration 在 `task` 表添加：`expected_online_time: DateTime`, `T_reported_complete_time: Date`
- [ ] 更新 SQLModel `Task` 模型添加新字段
- [ ] 运行迁移验证成功