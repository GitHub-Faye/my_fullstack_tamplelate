# 15 — 管理功能: 规则配置

**What to build:** 管理端规则配置完整功能：查看规则列表、创建/更新规则（星点奖励、完成判定、工资公式、系统参数）。

**Blocked by:** 04 — Prefactor: 创建客资和规则配置模型

**Status:** ready-for-agent

- [ ] 后端：创建 domains/system-rule 模块
- [ ] 后端：实现 SystemRule API（GET /system-rules, POST /system-rules, PUT /system-rules/{id}）
- [ ] 后端：规则分类：starpoint_reward, completion_judgment, salary_formula, system_param
- [ ] 后端：预置默认规则（星点奖励规则、完成判定规则）
- [ ] 后端：权限控制（仅管理员可操作）
- [ ] 前端：管理端规则配置页面（/admin/rules）
- [ ] 前端：规则列表（按分类分组）
- [ ] 前端：编辑规则弹窗
- [ ] 前端：规则修改历史查看
- [ ] 测试：API 集成测试