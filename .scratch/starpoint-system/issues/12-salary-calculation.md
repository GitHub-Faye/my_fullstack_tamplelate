# 12 — 核心流程: 工资试算与查看

**What to build:** 工程师和 PM 查看工资试算结果，管理员查看全员工资汇总并导出。

**Blocked by:** 11 — 核心流程: 星点计算与查看

**Status:** ready-for-agent

- [ ] 后端：创建 domains/salary 模块
- [ ] 后端：实现工资计算逻辑（工程师：S下 = (S0 - P差额) × K）
- [ ] 后端：实现 PM 工资计算逻辑（S总 = S底 + S考）
- [ ] 后端：实现 Salary API（GET /salaries/my, GET /salaries, POST /salaries/export）
- [ ] 后端：管理员设置工资参数 API（PUT /users/{id}/salary-params）
- [ ] 前端：工程师收入试算页面（/engineer/salary）
- [ ] 前端：PM 收入试算页面（/pm/salary）
- [ ] 前端：管理端工资管理页面（/admin/salaries）
- [ ] 前端：全员工资汇总表
- [ ] 前端：导出工资表功能（CSV）
- [ ] 前端：设置工程师工资参数弹窗
- [ ] 测试：单元测试（工资计算逻辑）
- [ ] 测试：集成测试（工资查询和导出）