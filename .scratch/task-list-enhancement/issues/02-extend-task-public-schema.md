# 02 — 后端 Schema：扩展 TaskPublic 暴露缺失字段

**What to build:** 扩展 `TaskPublic` schema 暴露 `progress`, `expected_online_time`, `T_reported_complete_time`, `pm_name`, `engineer_name` 字段，并更新 repository 查询逻辑。

**Blocked by:** #01 — 数据库迁移完成后

**Status:** ready-for-agent

- [ ] 在 `TaskPublic` 添加：`expected_online_time`, `T_reported_complete_time`, `progress`, `pm_name`, `engineer_name`
- [ ] 更新 repository 查询：JOIN user 表获取 `pm_name` 和 `engineer_name`
- [ ] 更新 `TasksPublic` 分页响应结构（如无变化则跳过）
- [ ] 确保 SDK 类型重新生成（`pnpm gen:sdk` 或手动同步）

## 补充：筛选参数扩展

`GET /tasks` 端点需暴露以下查询参数：

- `pm_id: str | None` — 按发布人 PM ID 过滤（所有角色均可使用）
- `task_type: str | None` — 按任务类型过滤（正常/紧急/便捷）
- `engineer_id: str | None` — 按工程师 ID 过滤

**权限逻辑**：
- 管理员：可查看全部任务，可传任意筛选参数
- PM：可查看全部任务，`pm_id` 由前端控制：
  - 「我发布的」→ 传 `pm_id=current_user.id`（筛选自己的任务）
  - 「其他PM」→ 传 `pm_id=current_user.id` + `exclude_pm_id=true`（排除自己的任务）
  - 「全部」→ 不传 `pm_id`（不过滤）
- 工程师：查看竞价中的任务列表（`status=bidding`），不过滤 `pm_id`