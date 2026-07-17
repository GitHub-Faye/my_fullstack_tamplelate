# 19 — 增强功能: 站内消息通知

**What to build:** 站内消息系统：任务状态变更通知、竞价结果通知、日报提交提醒、审批结果通知。

**Blocked by:** 08 — 核心流程: 竞价中标自动计算

**Status:** ready-for-agent

- [ ] 后端：创建 Notification 模型（字段：id, user_id, type, title, content, is_read, created_at）
- [ ] 后端：实现 Notification API（GET /notifications, POST /notifications/{id}/read）
- [ ] 后端：任务状态变更时创建通知
- [ ] 后端：竞价结果通知
- [ ] 后端：日报提交提醒（定时任务）
- [ ] 前端：消息中心组件（导航栏消息图标）
- [ ] 前端：消息列表弹窗
- [ ] 前端：未读消息数量显示
- [ ] 前端：消息详情查看
- [ ] 测试：API 集成测试