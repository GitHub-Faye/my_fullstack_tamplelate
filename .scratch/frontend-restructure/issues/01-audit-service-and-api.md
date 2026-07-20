# 01 — 审计日志统一服务 + 公共查询 API

**What to build:** 重构审计日志模块，实现统一的服务层接口和公共查询 API，让所有角色都能查看操作日志（管理员全量，PM/工程师仅自己）。

**Blocked by:** None — 可以立即开始

**Status:** ready-for-agent

- [ ] 在 `audit/` 模块创建 `service.py`，封装 `create_audit_log` 为统一入口，自动处理 `ip_address` 和 `user_id`
- [ ] 创建 `audit/router.py`，`GET /v1/audit-logs` 支持 `user_id`、`action`、`target_type`、`start_time`、`end_time` 筛选参数
- [ ] 扩展 `AuditLogPublic` schema 增加 `user_name` 字段（从 User 表 join 查询填充）
- [ ] 权限规则：管理员查全量（可传任意 user_id），PM/工程师强制查自己
- [ ] 注册新路由到 `v1/api.py`，标签为 `audit-logs`
- [ ] 编写测试：权限测试、筛选测试、分页测试、user_name 填充测试