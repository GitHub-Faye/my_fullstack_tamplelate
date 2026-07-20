# 05 — 前端路由重构：管理员工作区

**What to build:** 重构管理员前端路由，将 `/dashboard/admin/*` 改为 `/dashboard/*` 结构，分离数据概览、任务管理、工资管理、角色管理、账号管理、规则配置、操作日志页面。

**Blocked by:** #01 — 审计日志 API 完成后

**Status:** ready-for-agent

- [ ] 创建 `/dashboard/` 各页面路由：tasks、salaries、roles、users、rules、logs
- [ ] `/dashboard/page.tsx` 保持为数据概览，调用 `/v1/dashboard/admin`
- [ ] `/dashboard/tasks/page.tsx` 管理员任务管理表格
- [ ] `/dashboard/salaries/page.tsx` 工资管理页面（迁移现有内容）
- [ ] `/dashboard/roles/page.tsx` 角色管理页面
- [ ] `/dashboard/users/page.tsx` 账号管理页面（迁移现有 `/dashboard/admin` 内容）
- [ ] `/dashboard/rules/page.tsx` 规则配置页面
- [ ] `/dashboard/logs/page.tsx` 全量操作日志页面，调用 `GET /v1/audit-logs`
- [ ] 设置旧路由 `/dashboard/admin/*` 301 重定向到新路由
- [ ] 更新导航栏，管理员角色显示所有管理入口