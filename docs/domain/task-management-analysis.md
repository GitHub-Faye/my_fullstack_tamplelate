# 任务管理业务 — 完整领域分析报告

## 一、任务属性（Task 数据模型）

根据 PRD v4.0 和三个端原型，任务模型的完整属性如下：

| 字段 | 类型 | 说明 | 来源 |
|------|------|------|------|
| id | UUID | 主键 | 自增 |
| name | string | 任务名称 | PM/管理员创建时填写 |
| description | string? | 任务描述 | PM/管理员创建时填写 |
| task_type | enum: normal/urgent/convenient | 任务类型 | 创建时指定，管理员可转换 |
| status | enum | 任务状态（见下面状态机） | 随操作流转 |
| pm_id | UUID | 发布人（PM）ID | 创建时绑定 |
| engineer_id | UUID? | 执行工程师ID | 中标/指派后设置 |
| T_reported | float? | T报（工程师报价工时） | 中标时从报价确定，紧急/便捷任务直接设定 |
| T_actual | float? | T实（实际结算工时） | 完成时填入 |
| progress | string? | 进度描述（如"开发中 / 65%"） | 日报同步 |
| expected_online_time | datetime? | 预期上线时间 | PM/管理员设置 |
| T_reported_complete_time | datetime? | T报完成上报时间 | 日报提交时更新 |
| bidding_deadline | datetime? | 竞价截止时间 | 发布到竞价池时设置 |
| created_at | datetime | 创建时间 | 自动 |
| updated_at | datetime | 更新时间 | 自动 |

**当前缺失的属性（原型中有但模型没有）：**
- ✅ `attachment` 关联 (已有 Attachment 模型，但未暴露到 TaskPublic)
- ❌ `资料完整度`（原型详情页展示，非数据库字段，前端可计算）
- ❌ `T报完成时间` (已有 `T_reported_complete_time` 字段)
- ✅ `报价倒计时` (前端根据 `bidding_deadline` 实时计算)

---

## 二、任务状态机图（完整版）

### 原始 PRD 状态流转图（v4.0）

```
flowchart LR
    A[未确认] -->|管理员审核| B[已确定未发布]
    B -->|发布| C[竞价中]
    C -->|报价截止/中标| D[待启动]
    D -->|工程师启动| E[进行中]
    E -->|申请暂停| F[暂停中]
    F -->|恢复| E
    E -->|完成| G[已完成]
    D -->|拒绝| H[重新竞价]
    H --> C
    C -->|改为紧急| I[紧急指派]
    I --> D
```

### 当前代码实现的状态机（已包含 pause_requested）

```
flowchart LR
    A[unconfirmed] -->|管理员审核通过| B[unconfirmed]
    B -->|管理员发布| C[bidding]
    C -->|报价截止/中标| D[pending_start]
    D -->|工程师启动| E[in_progress]
    D -->|工程师拒绝| C[bidding]
    E -->|工程师申请暂停| F[pause_requested]
    F -->|管理员审批通过| G[paused]
    F -->|管理员驳回暂停| E
    G -->|工程师恢复| E
    G -->|管理员恢复| E
    E -->|工程师完成| H[completed]
    A -->|管理员驳回| A[保持 unconfirmed]
    D -->|管理员改派| D[保持 pending_start，更换 engineer_id]
    C -->|PM撤回| A[回到 unconfirmed]
```

### 完整状态节点（8个状态）

| 状态 | 枚举值 | 中文标签 | 说明 |
|------|--------|---------|------|
| 未确认 | `unconfirmed` | 未确认 | PM刚发布，待管理员审核 |
| 已确定未发布 | `unconfirmed` | 已确认未发布 | 管理员审核通过，尚未发布 |
| 竞价中 | `bidding` | 竞价中 | 工程师报价阶段 |
| 待启动 | `pending_start` | 待启动 | 已中标/指派，等待工程师启动 |
| 进行中 | `in_progress` | 进行中 | 开发执行中 |
| 暂停待审批 | `pause_requested` | 暂停待审批 | 工程师申请暂停，待管理员审批 |
| 暂停中 | `paused` | 暂停中 | 管理员审批通过，任务暂停 |
| 已完成 | `completed` | 已完成 | 任务完成并归档（终态） |

---

## 三、角色 × 状态 × 操作矩阵

### 工程师操作

| 状态 | 可执行操作 | 原型中按钮 | 后端 API |
|------|-----------|-----------|---------|
| 竞价中(bidding) | 报价，输入 T报 | "报价" | `POST /{task_id}/bids` |
| 待启动(pending_start) | 启动、拒绝 | "启动"、"拒绝" | `POST /{task_id}/start`、`POST /{task_id}/decline` |
| 进行中(in_progress) | 申请暂停 | "申请暂停/顺延" | `POST /{task_id}/pause-request` |
| 暂停中(paused) | 恢复任务 | "恢复" | `POST /{task_id}/resume` |
| 已完成(completed) | 查看归档日志 | "详情" | `GET /{task_id}` |

### PM操作

| 状态 | 可执行操作 | 原型中按钮 | 后端 API |
|------|-----------|-----------|---------|
| 未确认(unconfirmed) | 编辑资料、删除 | "编辑"、"删除" | `PUT /{task_id}`、`DELETE /{task_id}` |
| 已确定未发布(unconfirmed) | 编辑 | "编辑" | `PUT /{task_id}` |
| 竞价中(bidding) | 编辑资料、查看报价记录、撤回 | "编辑"、"报价记录"、"撤回" | `PUT /{task_id}`、`POST /{task_id}/withdraw` |
| 待启动(pending_start) | 查看日志 | "查看日志" | 前端路由 |
| 进行中(in_progress) | 资料变更、查看工作日志 | "资料变更"、"工作日志" | 前端路由 |
| 暂停中(paused) | 查看暂停记录 | "查看暂停记录" | 前端路由 |
| 已完成(completed) | 查看归档日志 | "查看归档日志" | 前端路由 |

### 管理员操作

| 状态 | 可执行操作 | 原型中按钮 | 后端 API |
|------|-----------|-----------|---------|
| 未确认(unconfirmed) | 审核通过、驳回、改为紧急/便捷 | "补充/发布"、"驳回" | `POST /{task_id}/approve`、`POST /{task_id}/reject`、`POST /{task_id}/convert-urgent\|convert-convenient` |
| 已确定未发布(unconfirmed) | 发布到竞价池、驳回、改为紧急/便捷 | "发布到竞价池"、"驳回" | `POST /{task_id}/publish` |
| 竞价中(bidding) | 查看报价、改为紧急/便捷 | "查看报价"、"改为紧急/便捷" | `POST /{task_id}/convert-urgent\|convert-convenient` |
| 待启动(pending_start) | 改派工程师 | "改派工程师" | `POST /{task_id}/reassign` |
| 进行中(in_progress) | 查看操作日志 | "操作日志" | 前端路由 |
| 暂停待审批(pause_requested) | 审批暂停、驳回暂停 | （原型无直接展示，但后端有 API） | `POST /{task_id}/pause-approve`、`POST /{task_id}/pause-reject` |
| 暂停中(paused) | 恢复任务、查看操作日志 | "恢复任务"、"操作日志" | `POST /{task_id}/restore` |
| 已完成(completed) | 查看操作日志 | "操作日志" | 前端路由 |

---

## 四、状态变更触发逻辑

### 自动触发逻辑

| 触发事件 | 条件 | 动作 | 后端实现 |
|---------|------|------|---------|
| 报价窗口截止 | bidding_deadline 到达 | 系统自动计算平均报价，确定中标人，状态变更为 pending_start | Celery 定时任务 `settle_bidding_task` |
| 日报阶段标记"已完成" | 日报提交时 current_stage = completed | 触发完成判定，计算星点 | 日报提交后触发 `trigger_starpoint_calculation` |
| 日报提交 | 工程师提交日报 | 累加 T_actual，同步 progress | DailyReport 创建时更新 Task |

### 联动规则

| 触发条件 | 联动效果 | 说明 |
|---------|---------|------|
| 工程师完成(complete) | 触发星点计算 | `trigger_starpoint_calculation` 根据 T_actual vs T_reported 计算星点变化 |
| 管理员改派(reassign) | 记录 AuditLog | 记录操作日志 |
| 管理员审核通过(approve) | 状态变为 unconfirmed | 记录 AuditLog |
| PM撤回(withdraw) | 清除 bidding_deadline，清空 engineer_id | 回到 unconfirmed |
| 工程师拒绝(decline) | 清空 engineer_id，设置新的 bidding_deadline | 重新进入竞价 |
| 管理员创建紧急/便捷任务 | 直接设置 engineer_id，状态设为 pending_start | 跳过竞价流程 |

---

## 五、后端代码清单

### 已实现（需要修改）

| 文件 | 路径 | 修改内容 |
|------|------|---------|
| Task 模型 | `apps/api/app/core/models.py` | 新增 `pause_requested` 状态，确认 `completed` 为终态 ✅ |
| Task 路由 | `apps/api/app/domains/task/router.py` | ✅ 路由已包含所有 8 个状态的 API |
| Task schemas | `apps/api/app/domains/task/schemas.py` | ✅ 已包含 TaskPublic |
| Task repository | `apps/api/app/domains/task/repository.py` | ✅ 已包含 CRUD |
| Task dependencies | `apps/api/app/domains/task/dependencies.py` | ✅ 已包含权限检查 |
| 合约 | `packages/contracts/src/task.ts` | 确认包含 8 个状态 ✅ |

### 需要新增的后端代码

| 优先级 | 需要新增 | 说明 |
|--------|---------|------|
| P0 | 管理员端任务管理页 | 原型中的"任务管理"页面，需要筛选、操作列 |
| P0 | PM端任务管理页补全 | 编辑/删除/撤回/资料变更等操作 |
| P0 | 工程师端任务管理页补全 | 启动/拒绝/暂停/恢复/报价 |
| P1 | 任务详情页（三端统一） | 查看完整任务信息、附件、日志 |
| P1 | 报价记录弹窗 | 管理员/PM查看报价列表 |
| P1 | 操作日志弹窗 | 查看任务操作历史 |
| P1 | 工作日志弹窗 | 查看日报列表 |
| P1 | 日报管理 | 提交日报、查看历史日报 |
| P2 | 任务管理页"报价倒计时"列 | 管理员端增加 |
| P2 | 任务类型转换弹窗 | 管理员端改为紧急/便捷 |

---

## 六、前端页面清单

### 管理员端页面

| 页面 | 路由 | 说明 | 实现状态 |
|------|------|------|---------|
| 数据概览 | `/admin` | 指标卡、工程师负载、星点排行、PM客资、收入统计 | ✅ 已实现 |
| **任务管理** | **`/admin/tasks`** | **任务列表+筛选+操作菜单** | **⚠️ 部分实现** |
| 任务详情 | `/admin/tasks/[id]` | 详情+审核操作+发布操作+类型转换 | ✅ 已实现 |
| 工资管理 | `/admin/salaries` | 工程师工资表、PM工资表 | ✅ 已实现 |
| 角色管理 | `/admin/roles` | 角色增删改、权限配置 | ✅ 已实现 |
| 账号管理 | `/admin/people` | 人员增删改查、禁用 | ✅ 已实现 |
| 规则配置 | `/admin/rules` | 星点/工资/客资/完成判定规则 | ✅ 已实现 |
| 操作日志 | `/admin/logs` | 全量操作日志 | ✅ 已实现 |

### PM端页面

| 页面 | 路由 | 说明 | 实现状态 |
|------|------|------|---------|
| PM工作台 | `/pm` | 指标卡、任务管理 | ✅ 已实现 |
| **任务管理** | **`/pm/tasks`** | **任务列表+筛选+操作** | **⚠️ 部分实现** |
| 发布任务 | `/pm/tasks/new` | 创建任务表单 | ⚠️ 已实现 |
| 编辑任务 | `/pm/tasks/[id]/edit` | 编辑任务表单 | ⚠️ 已实现 |
| 操作日志 | `/pm/logs` | 本人操作日志 | ✅ 已实现 |

### 工程师端页面

| 页面 | 路由 | 说明 | 实现状态 |
|------|------|------|---------|
| 工程师工作台 | `/engineer` | 指标卡、双标签页任务管理 | ✅ 已实现 |
| **任务管理** | **`/engineer/tasks`** | **"我的任务"+"竞价任务"标签** | **⚠️ 部分实现** |
| 操作日志 | `/engineer/logs` | 本人操作日志 | ✅ 已实现 |

### 前端需要修改/新增的组件

| 组件 | 文件 | 修改内容 |
|------|------|---------|
| EngineerTaskTable | `apps/web/features/task/client/EngineerTaskTable.tsx` | 补充"暂停中"状态的"恢复"按钮，补充详情弹窗完整字段 |
| PMTaskTable | `apps/web/features/task/client/PMTaskTable.tsx` | 确认操作列与原型一致，补充"已确定未发布"状态的编辑操作 |
| AdminTaskTable | `apps/web/features/task/client/AdminTaskTable.tsx` | 增加"报价倒计时"列，增加"暂停待审批"状态筛选，补充"暂停审批"操作 |
| AdminTaskDetail | `apps/web/features/task/client/AdminTaskDetail.tsx` | 增加"暂停待审批"状态的审批/驳回操作、改派操作 |
| TaskDetailDialog | `apps/web/features/task/client/TaskDetailDialog.tsx` | 补全工程师姓名、T实显示 |
| TaskCreateForm | `apps/web/features/task/client/TaskCreateForm.tsx` | 补充预期上线时间、附件上传 |
| TaskEditForm | `apps/web/features/task/client/TaskEditForm.tsx` | 确认已确定未发布状态也可编辑 |

---

## 七、原型与当前代码的差异分析

### 关键差异

1. **PRD 状态机缺少 "暂停待审批"(pause_requested)**：原型中工程师点击"申请暂停/顺延"后，应由管理员审批，但 PRD 的流转图直接跳转到"暂停中"。当前代码已实现 pause_requested 状态，这是正确的。

2. **PRD 报价窗口 24小时 vs 代码默认 3 天**：当前代码 `publish_task` 默认 `bidding_days=3`（3天），但 PRD 规定 24小时窗口。需改为 1 天。

3. **原型中"报价倒计时"列**：管理员端原型表格有"报价倒计时"列，当前 AdminTaskTable 没有。

4. **原型中"改为紧急/便捷"操作**：管理员端原型对竞价中任务显示"改为紧急/便捷"链接，当前 AdminTaskTable 的 bidding 状态已有此操作 ✅。

5. **原型中"暂停待审批"状态在管理员端**：原型未显示 pause_requested 状态，但代码中已有 pause-approve 和 pause-reject API。

6. **原型中"暂停记录"查看**：PM端原型中暂停中任务有"查看暂停记录"操作，当前代码未实现对应功能。

### 原型中"拒绝"操作的行为差异

- 工程师端原型："拒绝"按钮出现在待启动任务上，拒绝后任务重新进入竞价（代码中 `decline_task` 正确实现 ✅）
- 紧急/便捷任务拒绝：原型中提示"拒绝被指派紧急任务会自动扣分"，但代码中 `decline_task` 对所有类型任务都回到 bidding，未区分紧急任务

### 原型中"改派工程师"操作

- 管理员端原型：待启动任务显示"指派"操作，代码中 `reassign_task` 已实现 ✅
- 但原型中竞价中任务也有"查看报价"+"改为紧急/便捷"，改派只在待启动状态显示