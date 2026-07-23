# 03 — PM端任务列表对齐原型

**What to build:** PM 在 `/pm` 页面看到与原型一致的任务管理操作列。当前 `PMTaskTable` 已经通过 `getPmActions` 获取操作列表，需要确保所有状态的操作按钮与原型一致：

- 未确认(unconfirmed) → "编辑"、"删除" ✅ 已有，确认正常
- 已确定未发布(confirmed_unpublished) → 新增"编辑"按钮（当前缺失）
- 竞价中(bidding) → "编辑"、"报价记录"、"撤回" ✅ 已有
- 待启动(pending_start) → "查看日志" ✅ 已有
- 进行中(in_progress) → "资料变更"、"工作日志" ✅ 已有
- 暂停中(paused) → "查看暂停记录" ✅ 已有
- 已完成(completed) → "查看归档日志" ✅ 已有

主要修改：
1. `getPmActions` 函数增加 `confirmed_unpublished` 状态的"编辑"操作
2. 确保"资料变更"操作路由到正确的编辑页面（`/pm/tasks/[id]/edit`）
3. 表格列顺序与原型一致（9列）

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] confirmed_unpublished 状态增加"编辑"按钮
- [ ] 资料变更操作路由到编辑页面
- [ ] 表格列顺序与原型一致