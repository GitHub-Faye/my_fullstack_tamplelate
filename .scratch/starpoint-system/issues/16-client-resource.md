# 16 — 增强功能: PM 客资管理

**What to build:** PM 端客资管理完整功能：录入客资数据、查看历史记录、管理员查看汇总。

**Blocked by:** 04 — Prefactor: 创建客资和规则配置模型

**Status:** ready-for-agent

- [ ] 后端：创建 domains/client-resource 模块
- [ ] 后端：实现 ClientResource API（POST /client-resources, GET /client-resources）
- [ ] 后端：管理员设置 PM 客资参数 API（PUT /users/{id}/client-resource-params）
- [ ] 后端：权限控制（PM 录入自己的客资，管理员查看所有）
- [ ] 前端：PM 客资管理页面（/pm/client-resources）
- [ ] 前端：录入客资弹窗
- [ ] 前端：客资历史记录列表
- [ ] 前端：管理端 PM 客资汇总
- [ ] 测试：API 集成测试