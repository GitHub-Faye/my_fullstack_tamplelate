# 01 — 后端：扩展 PMDashboard 返回环比数据与分状态任务计数

**What to build:** 扩展 `GET /v1/dashboard/pm` 接口返回的 PMDashboard DTO，添加环比数据字段和分状态任务计数字段，使 PM 工作台指标卡能展示完整信息。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

### 需要添加的字段

**环比数据（客资指标）：**
- `last_month_new_clients: int` — 上月新增客资数（用于 "本月新增客资" 指标的环比对照）
- `yesterday_new_clients: int` — 昨日新增客资数（用于 "今日新增客资" 指标的环比对照）

**分状态任务计数（替代当前 `pm_task_count` 总数）：**
- `task_count_unconfirmed: int` — 未确认
- `task_count_bidding: int` — 竞价中
- `task_count_in_progress: int` — 进行中
- `task_count_completed: int` — 已完成
- `task_count_paused: int` — 暂停中
- （保留 `pm_task_count` 作为总数，或用 sum 替代）

**收入明细 URL（用于 "查看明细" 链接）：**
- `salary_detail_url: str` — 暂时为空字符串，前端显示占位提示

### 修改文件

1. `apps/api/app/domains/dashboard/schemas.py` — PMDashboard 类新增字段
2. `apps/api/app/domains/dashboard/repository.py` — `get_pm_dashboard` 新增查询逻辑
3. `packages/sdk/` — 重新生成 SDK 类型（或手动同步前端类型）
4. `apps/web/features/dashboard/api/client/queries.ts` — 更新 `PMDashboardData` 类型
5. `apps/api/tests/test_dashboard_api.py` — 更新测试

### 验收标准

- [ ] PMDashboard 返回上月新增客资、昨日新增客资
- [ ] PMDashboard 返回各状态任务计数
- [ ] 现有测试仍通过，新字段有测试覆盖
- [ ] 前端 SDK 类型与后端一致