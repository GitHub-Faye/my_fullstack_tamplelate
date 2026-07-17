# 03 — Prefactor: 创建日报和星点基础模型

**What to build:** 创建 DailyReport、StarPoint 数据模型及对应迁移，建立日报填报和星点系统的数据基础。

**Blocked by:** 02 — Prefactor: 创建任务管理基础模型

**Status:** ready-for-agent

- [ ] 创建 DailyReport 模型（字段：id, engineer_id, task_id, today_hours, current_stage, progress, completion_judgment, starpoint_change, notes, summary, has_blocker, report_date, created_at）
- [ ] DailyReport 阶段枚举：developing, testing, completed, paused
- [ ] 创建 StarPoint 模型（字段：id, engineer_id, task_id, change_amount, reason, judgment_type, T_reported, T_actual, created_at）
- [ ] 生成 Alembic 迁移文件
- [ ] 更新 Scope 定义，新增 report:*, starpoint:* 等