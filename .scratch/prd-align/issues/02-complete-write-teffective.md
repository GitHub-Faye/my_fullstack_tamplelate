# 02 — 任务完成时写入 T_effective

**What to build:** 在任务完成的两个路径中，系统自动设置 `T_effective = min(T_actual, T_reported)`：

1. `complete_task` 端点（工程师点击完成任务按钮）
2. 日报提交时 `current_stage == COMPLETED`（日报中标记任务完成）

T_actual 保持实际累计值不变（用于星点计算），T_effective 是截断后的有效工时（用于工资计算）。

**Blocked by:** 01（依赖 T_effective 字段存在）

**Status:** ready-for-agent

- [ ] `task/router.py` 的 `complete_task` 中，设置 COMPLETED 时写入 `task.T_effective = min(task.T_actual or 0, task.T_reported or 0)`
- [ ] `daily_report/router.py` 的 `create_daily_report` 中，stage 变为 COMPLETED 时写入同样的逻辑
- [ ] 验证：完成任务后查数据库，T_effective 值为 min(T_actual, T_reported)