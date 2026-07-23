# 05 — 后端 TaskPublic 增加姓名字段 + 报价窗口默认值修正

**What to build:** 两个后端修改：

1. **TaskPublic 增加 pm_name 和 engineer_name 字段：** 当前前端通过 `userMap` 在客户端查找姓名，但 userMap 可能不完整。后端 `Task` 模型通过 `pm` 和 `engineer` 关系可以获取姓名，应在 `TaskPublic` schema 中直接输出姓名，减少前端依赖。

2. **publish_task 的 bidding_days 默认值从 3 改为 1：** PRD 规定报价窗口为 24 小时，当前代码默认 3 天。修改 `router.py` 中 `publish_task` 的 `bidding_days` 参数默认值。

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] TaskPublic 增加 pm_name 和 engineer_name 字段
- [ ] publish_task 的 bidding_days 默认值改为 1