# 09 — 核心流程: 工程师任务执行（启动/拒绝/暂停/恢复/完成）

**What to build:** 工程师端任务执行完整功能链路：查看待启动任务 → 启动/拒绝任务 → 执行中申请暂停 → 管理员审批暂停 → 恢复任务 → 标记完成。

**Blocked by:** 08 — 核心流程: 竞价中标自动计算

**Status:** ready-for-agent

- [ ] 后端：实现任务执行 API（POST /tasks/{id}/start, POST /tasks/{id}/reject, POST /tasks/{id}/pause-request, POST /tasks/{id}/resume, POST /tasks/{id}/complete）
- [ ] 后端：管理员审批暂停 API（POST /tasks/{id}/pause-approve）
- [ ] 后端：管理员改派 API（POST /tasks/{id}/reassign）
- [ ] 后端：权限控制（仅被指派的工程师可操作）
- [ ] 后端：状态流转校验（只能从 pending_start 启动，从 in_progress 申请暂停等）
- [ ] 前端：工程师我的任务列表页面（/engineer/tasks）
- [ ] 前端：待启动任务操作弹窗（启动/拒绝）
- [ ] 前端：进行中任务操作（申请暂停）
- [ ] 前端：暂停中任务操作（恢复）
- [ ] 前端：标记完成确认
- [ ] 前端：管理端任务改派功能
- [ ] 测试：API 集成测试