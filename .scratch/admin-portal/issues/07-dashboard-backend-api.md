# 07 — 后端：数据概览补充 API

**What to build:** 数据概览页面需要今日新增客资、本月新增客资、今日提交日志量、进行中任务分状态计数等数据，以及工程师负载列表（每个工程师的任务数、T月剩余、T报准确率、风险状态）。当前 `get_admin_dashboard` 返回值缺少这些字段。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] 增强 `get_admin_dashboard` 返回值：新增 `today_new_leads`、`month_new_leads`、`today_log_count`、`in_progress_normal`、`in_progress_urgent`、`in_progress_convenient` 等字段
- [ ] 新增工程师负载查询接口（每个工程师的任务数、T月剩余、T报准确率、风险状态）
- [ ] 更新 AdminDashboard schema
- [ ] 后端测试通过