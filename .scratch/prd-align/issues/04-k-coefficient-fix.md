# 04 — K系数 数值对齐 PRD

**What to build:** 星点排名系数按 PRD 规定更新：前 20% → 1.2，后 20% → 0.7（中间 60% 保持 1.0）。工程师工资试算和仪表盘中的 K 系数、排行榜中的 K 系数全部跟随新值。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] `calculate_k_coefficient` 中前 20% 从 1.1 改为 1.2
- [ ] 后 20% 从 0.9 改为 0.7
- [ ] 验证：排行榜中排名前 20% 的工程师 K 系数为 1.2，后 20% 为 0.7