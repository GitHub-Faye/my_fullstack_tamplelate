# 03 — 工资计算改用 T_effective + 公式对齐 PRD

**What to build:** 工程师工资计算引擎按 PRD 技术服务部考核办法重新实现：

- **共享查询改用 T_effective：** `get_engineer_monthly_hours` 改为取 `Task.T_effective` 之和（而非 T_actual）
- **H0 自动计算：** `H0 = S0 ÷ T月计划`，不再依赖管理员手动设置的 H0 字段。S0 和 T月计划 仍由管理员设置
- **P差额 公式修正：** `P差额 = (T月计划 - T有效) × H0`，衡量"本月未完成的工时价值"
- **最低工资保底：** `S下 = max(5000, (S0 - P差额) × K)`
- 同步更新 `get_engineer_loads` 共享查询中 T_actual 相关部分

工程师工资试算页面的数据跟随新公式。

**Blocked by:** 02（依赖 T_effective 有值）

**Status:** ready-for-agent

- [ ] `get_engineer_monthly_hours` 改为 sum(T_effective) 而非 sum(T_actual)
- [ ] `calculate_engineer_salary` 中 H0 改为 `S0 / T_monthly_plan` 自动计算
- [ ] P差额 改为 `max(0, T_monthly_plan - T_effective) × H0`
- [ ] 最终工资增加 `max(5000, ...)` 保底逻辑
- [ ] `get_engineer_loads` 中 T_actual 相关统计改用 T_effective
- [ ] 验证：S0=8000、T月计划=150h、T有效=140h、K=1.0 → 工资 = max(5000, (8000-(150-140)×(8000/150))×1.0)