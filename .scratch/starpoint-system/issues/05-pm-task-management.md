# 05 — 核心流程: PM 任务管理（创建/编辑/查看）

**What to build:** PM 端任务管理完整功能链路：创建任务 → 编辑任务 → 查看任务列表 → 查看任务详情。任务初始状态为"未确认"，等待管理员审核。

**Blocked by:** 02 — Prefactor: 创建任务管理基础模型

**Status:** ready-for-agent

- [ ] 后端：创建 domains/task 模块（schemas, repository, router, dependencies）
- [ ] 后端：实现 Task API（POST /tasks, GET /tasks, GET /tasks/{id}, PUT /tasks/{id}）
- [ ] 后端：任务状态自动设为 unconfirmed，pm_id 为当前用户
- [ ] 后端：权限控制（仅 PM 角色可创建，仅自己创建的可编辑）
- [ ] 前端：创建 features/task 模块（PM 视图）
- [ ] 前端：PM 任务列表页面（/pm/tasks）
- [ ] 前端：发布任务弹窗/页面（/pm/tasks/new）
- [ ] 前端：任务详情页面（/pm/tasks/[id]）
- [ ] 前端：编辑任务功能
- [ ] SDK：运行 pnpm generate 更新 SDK
- [ ] 测试：API 集成测试