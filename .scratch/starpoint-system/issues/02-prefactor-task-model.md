# 02 — Prefactor: 创建任务管理基础模型

**What to build:** 创建 Task、Bid、Attachment 数据模型及对应迁移，建立任务管理的数据基础。

**Blocked by:** 01 — Prefactor: 扩展 User 模型支持角色区分和工资字段

**Status:** ready-for-agent

- [ ] 创建 Task 模型（字段：id, name, description, task_type, status, pm_id, engineer_id, T_reported, T_actual, bidding_deadline, created_at, updated_at）
- [ ] Task 状态枚举：unconfirmed, confirmed_unpublished, bidding, pending_start, in_progress, paused, completed
- [ ] Task 类型枚举：normal, urgent, convenient
- [ ] 创建 Bid 模型（字段：id, task_id, engineer_id, T_reported, amount, created_at, updated_at）
- [ ] 创建 Attachment 模型（字段：id, task_id, file_name, file_path, file_size, uploaded_by, created_at）
- [ ] 生成 Alembic 迁移文件
- [ ] 更新 Scope 定义，新增 task:*, bid:* 等