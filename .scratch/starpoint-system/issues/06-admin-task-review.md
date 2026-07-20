# 06 — 核心流程: 管理员任务审核与发布

**What to build:** 管理端任务审核功能链路：查看未确认任务 → 审核通过/驳回 → 发布到竞价池。审核通过后状态变为"已确定未发布"，发布后状态变为"竞价中"。

**Blocked by:** 05 — 核心流程: PM 任务管理（创建/编辑/查看）

**Status:** completed

- [x] 后端：实现审核 API（POST /tasks/{id}/approve, POST /tasks/{id}/reject, POST /tasks/{id}/publish）
- [x] 后端：权限控制（仅管理员角色可操作）
- [x] 后端：任务类型转换 API（POST /tasks/{id}/convert-urgent, POST /tasks/{id}/convert-convenient）
- [x] 前端：管理端任务管理页面（/admin/tasks）
- [x] 前端：未确认任务审核弹窗
- [x] 前端：任务发布确认
- [x] 前端：任务类型转换操作
- [x] 测试：API 集成测试