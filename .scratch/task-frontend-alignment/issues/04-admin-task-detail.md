# 04 — 管理端任务详情对齐原型

**What to build:** 管理员在 `/admin/tasks/[id]` 页面看到与原型一致的任务详情和操作。当前 `AdminTaskDetail` 只处理了未确认(unconfirmed) 和已确定未发布(confirmed_unpublished) 状态的操作，需要补充：

- 暂停待审批(pause_requested) 状态 → "审批暂停"和"驳回暂停"按钮
- 暂停中(paused) 状态 → "恢复任务"按钮
- 待启动(pending_start) 状态 → "改派工程师"按钮（跳转到 `/admin/tasks/[id]?tab=assign`）
- 完成状态(completed) → "操作日志"按钮
- 任务详情信息展示：增加工程师姓名（从 userMap 获取）、T报/T实/进度等完整字段

**Blocked by:** Ticket 01 — 管理端任务列表对齐原型（详情页路由从列表跳转，需要先确保列表页可用）

**Status:** ready-for-agent

- [ ] 暂停待审批状态增加"审批暂停"和"驳回暂停"操作
- [ ] 暂停中状态增加"恢复任务"操作
- [ ] 待启动状态增加"改派工程师"操作
- [ ] 详情页展示工程师姓名、完整字段