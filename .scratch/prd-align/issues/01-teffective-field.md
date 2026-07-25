# 01 — Task 模型新增 T_effective 字段 + 数据库迁移

**What to build:** Task 表新增 `T_effective` 字段，用于存储任务完成时的有效工时（`min(T_actual, T_reported)`）。后续的工资计算和共享查询都将使用 T_effective 而非 T_actual。需同步更新 TaskPublic 等响应 schema 确保前端能读到该字段。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] TaskBase 模型新增 `T_effective: Optional[float] = Field(default=None, ge=0, description="T有效（任务完成时取 min(T_actual, T_reported)，用于工资计算）")`
- [ ] 同步更新 `TaskPublic` schema 包含 `T_effective` 字段
- [ ] 运行数据库迁移使新列生效
- [ ] 前端 SDK 重新生成（`pnpm run generate:local`）