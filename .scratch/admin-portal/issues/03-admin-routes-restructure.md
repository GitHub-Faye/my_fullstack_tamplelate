# 03 — 前端：管理员路由重构 + 导航栏

**What to build:** 将管理员页面从 `/dashboard` 路由组迁移到独立的 `/admin` 路由组，包含 7 个页面：数据概览、任务管理、工资管理、角色管理、账号管理、规则配置、操作日志。添加管理员左侧导航栏。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] 新增 `/admin` 路由组，7 个页面目录
- [ ] 管理员导航栏组件（左侧 7 项，高亮当前页，匹配 PRD 样式）
- [ ] 将现有 `/dashboard` 下的管理员页面内容迁移到 `/admin/*`
- [ ] 登录后角色跳转包含管理员路由 `/admin`
- [ ] 类型检查通过