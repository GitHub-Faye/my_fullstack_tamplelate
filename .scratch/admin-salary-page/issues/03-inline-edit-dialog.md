# 03 — 行内工资参数编辑弹窗

**What to build:** 管理员在工资汇总页面可直接编辑员工工资参数，无需跳转到用户管理页。工程师行可编辑 S0、T_monthly_plan；PM 行可编辑 S_base、S_assess、R_base、R_assess。用弹窗编辑并调用已有 PUT 接口保存。

**Blocked by:** #01 — 后端 Schema + Service、#04 — SDK 类型同步

**Status:** ready-for-agent

- [ ] 工程师行右侧加"编辑"按钮，点击弹窗修改：S0、T_monthly_plan
- [ ] PM 行右侧加"编辑"按钮，点击弹窗修改：S_base、S_assess、R_base、R_assess
- [ ] 调 `PUT /v1/salaries/users/{user_id}/params` 保存，保存成功后刷新列表
- [ ] 工程师弹窗不含 H0 字段（H0 为自动计算）
- [ ] 校验：S0/S_base >= 0、R_base/R_assess 0~1