# 04 — 前端路由重构：工程师工作区

**What to build:** 创建工程师前端路由 `/engineer`（工程师工作台，含个人指标 + 任务列表）和 `/engineer/logs`（操作日志页面）。

**Blocked by:** #01 — 审计日志 API 完成后

**Status:** ready-for-agent

- [ ] 创建 `/engineer/page.tsx` 工程师工作台页面：个人指标卡 + 任务列表
- [ ] 创建 `/engineer/logs/page.tsx` 工程师操作日志页面，调用 `GET /v1/audit-logs?user_id=current`
- [ ] 更新导航栏，工程师角色显示"工程师工作台"和"操作日志"入口
- [ ] 工程师任务列表聚焦于竞价和执行阶段任务