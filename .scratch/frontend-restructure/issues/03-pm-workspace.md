# 03 — 前端路由重构：PM 工作区

**What to build:** 重构 PM 前端路由，将 `/pm/tasks` 改为 `/pm`（PM 工作台），包含仪表盘指标卡 + 任务管理表格，并新增 `/pm/logs` 操作日志页面。

**Blocked by:** #01 — 审计日志 API 完成后

**Status:** ready-for-agent

- [ ] 创建 `/pm/page.tsx` PM 工作台页面：顶部 4 个指标卡（本月新增客资、今日新增客资、我发布的任务、收入试算），下方任务管理表格
- [ ] 创建 `/pm/logs/page.tsx` PM 操作日志页面，调用 `GET /v1/audit-logs?user_id=current`
- [ ] 更新导航栏，PM 角色显示"PM工作台"和"操作日志"入口
- [ ] `/pm/tasks` 设置 301 重定向到 `/pm`
- [ ] 创建 `features/audit-log/` 通用组件（AuditLogTable + AuditLogFilters）
- [ ] 调整 `features/task/` 组件复用结构