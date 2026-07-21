# 05 — 后端：更新审计日志查询接口支持筛选参数

**What to build:** 确保 `GET /v1/audit-logs` 接口支持筛选参数（日期范围、操作类型），当前可能已支持部分参数，如有缺失则补充。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

### 包含内容

- 确认审计日志列表接口是否支持 `start_date`、`end_date`、`action_type` 筛选参数
- 如不支持则补充实现
- 更新 SDK 类型定义

### 验收标准

- [ ] GET /v1/audit-logs 支持日期范围筛选
- [ ] GET /v1/audit-logs 支持操作类型筛选
- [ ] 现有测试通过