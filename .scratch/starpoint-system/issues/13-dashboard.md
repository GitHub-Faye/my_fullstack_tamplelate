# 13 — 管理功能: 数据概览与指标卡

**What to build:** 三端首页数据概览：工程师指标卡、PM 指标卡、管理员数据看板。

**Blocked by:** 12 — 核心流程: 工资试算与查看

**Status:** ready-for-agent

- [ ] 后端：创建 domains/dashboard 模块
- [ ] 后端：实现 Dashboard API（GET /dashboard/engineer, GET /dashboard/pm, GET /dashboard/admin）
- [ ] 后端：工程师指标：当前星点、本月剩余工时、收入试算、T报准确率
- [ ] 后端：PM 指标：今日新增客资、本月新增客资、收入试算
- [ ] 后端：管理员指标：今日新增客资、本月新增客资、今日提交日志量、进行中任务数、工程师负载、星点排行榜、收入统计
- [ ] 前端：工程师工作台首页（/engineer）
- [ ] 前端：PM 工作台首页（/pm）
- [ ] 前端：管理端数据概览页面（/admin）
- [ ] 前端：指标卡组件
- [ ] 前端：图表组件（任务分布、收入趋势）
- [ ] 测试：API 集成测试