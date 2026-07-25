# 06 — 弃单扣星点 -15

**What to build:** 工程师拒绝已中标但未启动的任务（PENDING_START 状态）时，系统自动扣减 15 星点，并创建一条星点变化记录（原因标注"弃单"）。工程师可在星点记录明细中看到该扣分项。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] `decline_task` 端点中增加星点扣减逻辑：`change_amount = -15`
- [ ] 创建对应的 `StarPointRecord`，reason 为"弃单（中标后未启动或启动后终止）"
- [ ] 更新工程师的 `current_starpoint`
- [ ] 验证：启动一个任务后弃单，星点减少 15，星点记录中出现对应条目