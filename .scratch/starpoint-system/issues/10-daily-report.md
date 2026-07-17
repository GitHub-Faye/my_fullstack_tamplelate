# 10 — 核心流程: 日报填报与查询

**What to build:** 工程师端日报填报完整功能链路：填写日报（今日投入、阶段、进度、说明）→ 查看历史日报 → PM/管理员查看日报。

**Blocked by:** 09 — 核心流程: 工程师任务执行（启动/拒绝/暂停/恢复/完成）

**Status:** ready-for-agent

- [ ] 后端：创建 domains/daily-report 模块
- [ ] 后端：实现 DailyReport API（POST /daily-reports, GET /daily-reports, GET /daily-reports/{id}）
- [ ] 后端：T实自动累加（根据今日投入）
- [ ] 后端：日报与任务联动（阶段、进度同步到任务）
- [ ] 后端：权限控制（工程师填报自己的日报，PM/管理员查看）
- [ ] 前端：工程师日报填报弹窗（/engineer/reports）
- [ ] 前端：日报表单（今日投入、阶段选择、进度、说明、总结）
- [ ] 前端：历史日报列表（按日期筛选）
- [ ] 前端：PM 查看工程师日报
- [ ] 前端：管理端日报汇总页面（/admin/reports）
- [ ] 测试：API 集成测试