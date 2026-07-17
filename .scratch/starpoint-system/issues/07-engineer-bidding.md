# 07 — 核心流程: 工程师竞价报价

**What to build:** 工程师端竞价报价完整功能链路：查看竞价中任务列表 → 查看任务详情 → 提交报价 → 修改报价 → 查看我的报价。

**Blocked by:** 06 — 核心流程: 管理员任务审核与发布

**Status:** in-progress

- [x] 后端：创建 domains/bid 模块
- [x] 后端：实现 Bid API（POST /tasks/{id}/bids, PUT /tasks/{id}/bids/{bid_id}, GET /tasks/{id}/bids）
- [x] 后端：报价金额自动计算（amount = H0 × T_reported）
- [x] 后端：权限控制（仅工程师角色可报价，报价窗口内可修改）
- [x] 后端：竞价任务列表 API（GET /tasks?status=bidding）
- [ ] 前端：工程师竞价任务列表页面（/engineer/bidding）
- [ ] 前端：任务详情弹窗（显示报价倒计时）
- [ ] 前端：提交报价弹窗（输入 T报，显示报价金额）
- [ ] 前端：我的报价列表
- [x] 测试：API 集成测试