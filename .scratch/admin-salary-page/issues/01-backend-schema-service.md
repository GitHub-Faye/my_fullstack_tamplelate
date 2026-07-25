# 01 — 后端 Schema + Service：新增明细响应、支持月份筛选

**What to build:** 管理员工资汇总页需要的完整后端数据支持。当前 `SalarySummary` 只返回 `salary` 一个字段，前端无法展示 H0、P差额、K系数等明细。需要新增明细 schema、支持按月份筛选工时、批量计算返回完整数据。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] `salary/schemas.py` 新增 `EngineerSalarySummary`（含 S0、H0、T_monthly_plan、T_effective、T_actual_monthly、T_reported_monthly、P_diff、k_coefficient、current_starpoint、salary_final）、`PMSalarySummary`（含 S_base、S_assess、R_base、R_assess、salary_total），修改 `SalarySummaryList` 为 Union 类型
- [ ] `shared/queries.py` 的 `get_engineer_monthly_hours` 增加可选 `month: Optional[str]` 参数（格式 `YYYY-MM`），按月份过滤 `Task.updated_at` 范围
- [ ] `salary/service.py` 的 `calculate_engineer_salary` 增加 `month` 透传到 `get_engineer_monthly_hours`；`calculate_all_salaries` 返回 `EngineerSalarySummary | PMSalarySummary` 列表而非 `SalarySummary`
- [ ] `salary/router.py` 的 `read_salary_summary` 增加 `month: Annotated[str, Query]` 参数，透传到 service 层
- [ ] 现有测试通过