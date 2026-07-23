# 01 — 管理端任务列表对齐原型

**What to build:** 管理员在 `/admin/tasks` 页面看到与原型一致的完整任务管理表格，包含：
- 完整的 11 列布局：任务名称、任务类型、发布人、工程师、状态、T报、T实、进度、预计上线时间、创建时间、操作
- 新增"报价倒计时"列（仅对竞价中任务显示倒计时，其他状态显示 `-`）
- 筛选栏增加"暂停待审批"(pause_requested) 状态选项
- 对暂停待审批状态的任务，DropdownMenu 中增加"审批暂停"和"驳回暂停"操作（调用后端 `POST /{task_id}/pause-approve` 和 `POST /{task_id}/pause-reject`）
- 增加"发布任务"按钮入口（管理员直接创建紧急/便捷任务，跳转到 `/admin/tasks/new` 或弹窗表单）
- 操作列使用 DropdownMenu 展示所有可用操作（与原型一致）

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] 管理员任务列表增加"报价倒计时"列，显示竞价中任务的倒计时
- [ ] 筛选栏增加 pause_requested 状态选项
- [ ] 暂停待审批任务的操作菜单增加"审批暂停"和"驳回暂停"
- [ ] 增加"发布任务"按钮入口
- [ ] 表格列顺序与原型一致（11列）