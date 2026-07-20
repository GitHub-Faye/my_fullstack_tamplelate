# 02 — 统一审计日志导入路径并补齐缺失的日志记录

**What to build:** 修复所有模块中 `create_audit_log` 的错误导入路径，并补齐所有业务操作中缺失的审计日志记录。

**Blocked by:** #01 — 审计日志统一服务完成后

**Status:** ready-for-agent

- [ ] 修复 `task/router_admin.py` 从 `app.domains.user.repository` 导入 → 改为 `app.domains.audit.service`
- [ ] 审计所有现有 `create_audit_log` 调用改为统一从 `audit.service` 导入
- [ ] 补齐缺失的审计日志记录：task 创建/更新/删除、task 审批/拒绝/发布/转换类型/重新分配、task 开始/完成/暂停/恢复、user 创建/更新/删除/启用/禁用/重置密码、system_rule 创建/更新/删除、salary 更新
- [ ] 编写测试验证每个关键操作都正确记录审计日志