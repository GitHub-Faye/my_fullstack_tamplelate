# 04 — Prefactor: 创建客资和规则配置模型

**What to build:** 创建 ClientResource、SystemRule 数据模型及对应迁移，建立客资管理和规则配置的数据基础。

**Blocked by:** 01 — Prefactor: 扩展 User 模型支持角色区分和工资字段

**Status:** ready-for-agent

- [ ] 创建 ClientResource 模型（字段：id, pm_id, actual_count, baseline_count, date, created_at）
- [ ] 创建 SystemRule 模型（字段：id, category, name, applies_to, value, is_public, is_active, created_at, updated_at）
- [ ] SystemRule 分类枚举：starpoint_reward, salary_formula, client_resource, completion_judgment, system_param
- [ ] 生成 Alembic 迁移文件
- [ ] 更新 Scope 定义，新增 client-resource:*, rule:* 等