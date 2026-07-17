# 11 — 核心流程: 星点计算与查看

**What to build:** 任务完成后自动计算星点，工程师查看星点明细和排名，管理员查看排行榜。

**Blocked by:** 10 — 核心流程: 日报填报与查询

**Status:** ready-for-agent

- [ ] 后端：创建 domains/starpoint 模块
- [ ] 后端：实现星点计算逻辑（根据 T实/T报 比例）
- [ ] 后端：任务完成时触发星点计算
- [ ] 后端：紧急任务额外星点奖励（+15）
- [ ] 后端：实现 StarPoint API（GET /starpoints/my, GET /starpoints/leaderboard, POST /starpoints/adjust）
- [ ] 后端：K 系数计算（按星点排名分三档）
- [ ] 前端：工程师我的星点页面（/engineer/starpoints）
- [ ] 前端：星点明细列表
- [ ] 前端：管理端星点排行榜页面（/admin/starpoints）
- [ ] 前端：管理员手动调整星点功能
- [ ] 测试：单元测试（星点计算逻辑、K 系数计算）
- [ ] 测试：集成测试（完整星点流程）