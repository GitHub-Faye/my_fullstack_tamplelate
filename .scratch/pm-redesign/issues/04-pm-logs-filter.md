# 04 — 前端：PM 操作日志增强筛选

**What to build:** 增强 PMLogsPage 操作日志页面，补充日期范围筛选和操作类型筛选，复用 AuditLogFilters 组件，使 PM 能按时间范围和操作类型过滤自己的操作记录。

**Blocked by:** None — can start immediately（后端审计日志列表已支持筛选参数）

**Status:** ready-for-agent

### 包含内容

- 引入 `AuditLogFilters` 组件（已存在）
- PMLogsPage 页面顶部增加筛选栏：日期范围（开始日期 - 结束日期）+ 操作类型下拉
- 筛选条件联动到 `useAuditLogs` 的查询参数
- 页面标题改为 "本人相关操作日志"
- 保持表格列：时间、类型、内容

### 修改文件

- `apps/web/app/(dashboard)/pm/logs/page.tsx` — 增强筛选

### 验收标准

- [ ] PMLogsPage 显示日期范围和操作类型筛选
- [ ] 筛选条件正确传递到 API 请求
- [ ] 筛选后结果正确刷新
- [ ] 分页仍正常工作