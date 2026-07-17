# 01 — Prefactor: 扩展 User 模型支持角色区分和工资字段

**What to build:** 扩展现有 User 模型，添加角色字段（engineer/pm/admin）和工资相关字段（S0、H0、T月计划、星点等），为后续功能开发奠定数据基础。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] User 模型添加 `role` 字段（枚举：engineer/pm/admin）
- [ ] User 模型添加工程师工资字段：S0、H0、T_monthly_plan、current_starpoint
- [ ] User 模型添加 PM 工资字段：S_base、S_assess、R_base、R_assess
- [ ] 生成 Alembic 迁移文件
- [ ] 更新 Scope 定义，新增 user:admin 等
- [ ] 更新 contracts 包同步 Scope 定义
- [ ] 编写单元测试验证模型变更