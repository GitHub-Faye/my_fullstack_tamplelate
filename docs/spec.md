# 研发星点系统技术规格书

## Problem Statement

研发团队缺乏一套公平透明的任务分配与绩效考核系统。当前存在以下问题：

1. **任务分配不透明**：任务分配依赖人工协调，缺乏公平竞价机制
2. **绩效难以量化**：工程师交付质量（T实 vs T报）无法自动计算，工资核算依赖人工
3. **进度追踪分散**：日报填报缺乏统一平台，任务状态同步滞后
4. **数据决策困难**：管理层缺乏实时数据看板支撑决策

## Solution

构建一套面向研发团队的任务管理与绩效考核平台，覆盖三种角色：

- **工程师**：参与竞价报价、执行任务、填报日报、查看星点与收入试算
- **市场产品PM**：发布任务需求、跟踪任务进度、管理客资数据
- **管理员**：审核任务、指派人员、管理工资与规则、查看全量数据

系统以 **任务竞价** 为核心机制，**星点评分** 为绩效抓手，**日报填报** 为进度追踪手段，实现工资与绩效自动挂钩。

## User Stories

### 任务管理

1. As a 市场产品PM, I want to 创建新任务并填写任务名称、说明、附件, so that 工程师可以了解任务需求并参与竞价
2. As a 市场产品PM, I want to 编辑我发布的未确认任务, so that 修正需求描述错误
3. As a 市场产品PM, I want to 撤回竞价中的任务, so that 取消不再需要的需求
4. As a 管理员, I want to 审核PM提交的任务, so that 确保任务需求完整且合理
5. As a 管理员, I want to 驳回不合理的任务, so that 避免无效任务进入竞价
6. As a 管理员, I want to 发布已审核的任务到竞价池, so that 工程师可以开始报价
7. As a 管理员, I want to 将竞价中的任务改为紧急任务, so that 应对突发需求
8. As a 管理员, I want to 将竞价中的任务改为便捷任务, so that 快速分配小工作量任务
9. As a 管理员, I want to 查看所有任务的报价详情, so that 了解竞价情况
10. As a 管理员, I want to 查看任务的操作日志, so that 追溯任务变更历史

### 竞价与报价

11. As an 工程师, I want to 查看竞价中的任务列表, so that 发现可参与的任务
12. As an 工程师, I want to 查看任务详情（名称、说明、附件、报价倒计时）, so that 评估是否参与竞价
13. As an 工程师, I want to 提交我的报价（T报）, so that 参与任务竞价
14. As an 工程师, I want to 在报价窗口内修改我的报价, so that 调整预估工时
15. As an 工程师, I want to 查看我已报价的任务列表, so that 跟踪竞价状态
16. As a 市场产品PM, I want to 查看我发布的任务的报价情况, so that 了解工程师参与度
17. As a 系统, I want to 在报价窗口截止后自动计算平均报价, so that 确定中标人
18. As a 系统, I want to 选择报价最接近均价的工程师中标, so that 公平分配任务
19. As a 系统, I want to 在所有工程师报完价时提前截止竞价, so that 提高效率

### 任务执行

20. As an 工程师, I want to 查看待启动的任务列表, so that 了解已中标/指派给我的任务
21. As an 工程师, I want to 启动已中标的任务, so that 开始执行
22. As an 工程师, I want to 拒绝已中标的任务, so that 任务重新进入竞价
23. As an 工程师, I want to 在执行过程中申请暂停任务, so that 处理阻塞情况
24. As an 工程师, I want to 恢复暂停中的任务, so that 继续执行
25. As an 工程师, I want to 标记任务为已完成, so that 触发完成判定和星点计算
26. As a 管理员, I want to 审批工程师的暂停申请, so that 管理任务进度风险
27. As a 管理员, I want to 改派任务给其他工程师, so that 应对人员变动
28. As a 市场产品PM, I want to 查看我发布的任务的执行进度, so that 跟踪项目状态
29. As a 市场产品PM, I want to 变更任务的资料信息, so that 更新需求说明

### 日报填报

30. As an 工程师, I want to 每日填写工作日报, so that 记录工时投入和进度
31. As an 工程师, I want to 在日报中填写今日投入工时, so that 累加T实
32. As an 工程师, I want to 在日报中选择任务当前阶段（开发中/测试中/已完成/暂停中）, so that 更新任务状态
33. As an 工程师, I want to 在日报中填写当前进度百分比, so that 同步任务进度
34. As an 工程师, I want to 在日报中填写工作说明和今日总结, so that 记录工作内容
35. As an 工程师, I want to 标记是否存在阻塞, so that 申请暂停/顺延
36. As an 工程师, I want to 查看我的历史日报, so that 回顾工作记录
37. As an 工程师, I want to 按日期筛选历史日报, so that 快速定位特定日期记录
38. As a 市场产品PM, I want to 查看工程师的日报, so that 了解任务执行细节
39. As a 管理员, I want to 查看所有工程师的日报汇总, so that 监控团队工作状态
40. As a 管理员, I want to 提醒未提交日报的工程师, so that 确保日报及时填报

### 星点系统

41. As an 工程师, I want to 查看我当前的星点总数, so that 了解我的绩效状态
42. As an 工程师, I want to 查看我的星点明细（任务、T报、T实、完成判定、星点变化）, so that 了解星点增减原因
43. As an 工程师, I want to 查看我的星点排名, so that 了解我在团队中的相对位置
44. As a 系统, I want to 在任务完成时根据T实/T报比例自动计算星点变化, so that 量化交付质量
45. As a 系统, I want to 对紧急任务完成给予额外星点奖励（+15）, so that 激励紧急响应
46. As a 管理员, I want to 查看工程师星点排行榜, so that 了解团队绩效分布
47. As a 管理员, I want to 手动调整工程师的星点, so that 奖励/惩罚特殊行为

### 工资管理

48. As an 工程师, I want to 查看我的工资试算结果, so that 了解预计收入
49. As an 工程师, I want to 查看我的 S0（工资基数）、H0（基准时薪）、K系数, so that 了解工资构成
50. As an 工程师, I want to 查看我的 T有效（有效工时）累计, so that 了解工作量
51. As a 市场产品PM, I want to 查看我的收入试算结果, so that 了解预计收入
52. As a 市场产品PM, I want to 查看我的客资数据（L实、L基）, so that 了解考核进度
53. As a 管理员, I want to 查看全员工资汇总表, so that 进行工资核算
54. As a 管理员, I want to 导出工资表, so that 提交财务发薪
55. As a 管理员, I want to 设置工程师的 S0（工资基数）, so that 确定基础工资
56. As a 管理员, I want to 设置工程师的 H0（基准时薪）, so that 计算报价金额
57. As a 管理员, I want to 设置工程师的 T月计划, so that 确定月度计划工时
58. As a 管理员, I want to 手动调整工程师的工资（奖励/扣减）, so that 处理特殊情况
59. As a 管理员, I want to 设置 PM 的 S底、S考、R底、R考, so that 配置 PM 工资结构
60. As a 管理员, I want to 设置 PM 的 L基（基准客资数）, so that 确定 PM 考核目标

### 客资管理

61. As a 市场产品PM, I want to 录入我的客资数据, so that 记录客户资源增长
62. As a 市场产品PM, I want to 查看我的客资历史记录, so that 追踪客资增长趋势
63. As a 管理员, I want to 查看所有 PM 的客资汇总, so that 监控团队客资状况
64. As a 管理员, I want to 设置 PM 的基准客资数（L基）, so that 确定考核目标

### 规则配置

65. As a 管理员, I want to 配置星点奖励规则（阈值和星点变化）, so that 调整绩效激励政策
66. As a 管理员, I want to 配置完成判定规则, so that 调整质量评判标准
67. As a 管理员, I want to 配置工资计算公式参数, so that 调整工资核算逻辑
68. As a 管理员, I want to 配置报价窗口时长, so that 调整竞价周期
69. As a 管理员, I want to 配置标准月工时, so that 确定 H0 计算基准
70. As a 管理员, I want to 查看规则修改历史, so that 追溯规则变更

### 数据概览

71. As an 工程师, I want to 查看我的指标卡（当前星点、本月剩余工时、收入试算、T报准确率）, so that 快速了解我的工作状态
72. As a 市场产品PM, I want to 查看我的指标卡（今日新增客资、本月新增客资、收入试算）, so that 快速了解我的客资状态
73. As a 管理员, I want to 查看今日新增客资数量, so that 监控客资增长
74. As a 管理员, I want to 查看本月新增客资数量, so that 监控月度客资目标
75. As a 管理员, I want to 查看今日提交日志量, so that 监控日报提交情况
76. As a 管员, I want to 查看进行中任务数量（按类型细分）, so that 监控任务执行状态
77. As a 管理员, I want to 查看工程师负载统计（任务数、T月剩余、T报准确率）, so that 分配任务时参考
78. As a 管理员, I want to 查看工程师星点排行榜, so that 了解团队绩效分布
79. As a 管理员, I want to 查看PM客资列表, so that 了解各PM客资贡献
80. As a 管理员, I want to 查看收入统计（月度总收入、工程师成本、PM成本）, so that 了解团队成本

### 人员与账号管理

81. As a 管理员, I want to 创建新的工程师账号, so that 添加团队成员
82. As a 管理员, I want to 创建新的 PM 账号, so that 添加市场产品人员
83. As a 管理员, I want to 编辑用户信息（姓名、邮箱等）, so that 维护人员信息
84. As a 管理员, I want to 禁用/启用用户账号, so that 管理账号状态
85. As a 管理员, I want to 重置用户密码, so that 帮助用户恢复访问
86. As a 管理员, I want to 查看用户的操作日志, so that 追溯用户行为
87. As an 工程师, I want to 修改我的个人信息, so that 更新联系方式
88. As an 工程师, I want to 修改我的密码, so that 保护账号安全

### 权限与认证

89. As a 用户, I want to 使用邮箱和密码登录系统, so that 访问我的工作台
90. As a 用户, I want to 登出系统, so that 保护账号安全
91. As an 工程师, I want to 只能访问工程师端功能, so that 防止越权操作
92. As a 市场产品PM, I want to 只能访问 PM 端功能, so that 防止越权操作
93. As a 管理员, I want to 访问所有端的功能, so that 管理整个系统
94. As a 系统, I want to 根据用户角色自动路由到对应端, so that 简化用户导航

## Implementation Decisions

### 架构决策

1. **三端合一前端架构**（ADR-0001）
   - 单一 Next.js 应用，通过路由区分三端
   - 路由规划：`/engineer/*`、`/pm/*`、`/admin/*`
   - 通过中间件检查用户角色，自动重定向

2. **角色完全独立**（ADR-0004）
   - 用户表 `role` 字段为 `engineer` | `pm` | `admin` 之一
   - 不支持角色兼任，简化权限模型

### 数据模型

3. **任务模型**：新增 `Task` 表
   - 字段：id, name, description, task_type(enum), status(enum), pm_id, engineer_id, T_reported, T_actual, bidding_deadline, created_at, updated_at
   - 状态枚举：`unconfirmed`, `confirmed_unpublished`, `bidding`, `pending_start`, `in_progress`, `paused`, `completed`
   - 类型枚举：`normal`, `urgent`, `convenient`

4. **报价模型**：新增 `Bid` 表
   - 字段：id, task_id, engineer_id, T_reported, amount, created_at, updated_at
   - 一个任务可有多个报价，报价窗口内可修改

5. **日报模型**：新增 `DailyReport` 表
   - 字段：id, engineer_id, task_id, today_hours, current_stage, progress, completion_judgment, starpoint_change, notes, summary, has_blocker, report_date, created_at
   - 阶段枚举：`developing`, `testing`, `completed`, `paused`

6. **星点模型**：新增 `StarPoint` 表
   - 字段：id, engineer_id, task_id, change_amount, reason, judgment_type, T_reported, T_actual, created_at

7. **客资模型**：新增 `ClientResource` 表
   - 字段：id, pm_id, actual_count, baseline_count, date, created_at

8. **工资模型**：扩展 User 表
   - 新增字段：`S0`(工资基数), `H0`(基准时薪), `T_monthly_plan`(月计划工时), `current_starpoint`(当前星点), `K_coefficient`(K系数)
   - PM 用户新增：`S_base`(底薪), `S_assess`(考核部分), `R_base`(底薪比例), `R_assess`(考核比例)

9. **规则配置模型**：新增 `SystemRule` 表
   - 字段：id, category, name, applies_to, value, is_public, is_active, created_at, updated_at
   - 分类枚举：`starpoint_reward`, `salary_formula`, `client_resource`, `completion_judgment`, `system_param`

10. **附件模型**：新增 `Attachment` 表
    - 字段：id, task_id, file_name, file_path, file_size, uploaded_by, created_at

### API 设计

11. **任务 API**
    - `POST /api/v1/tasks` — PM 创建任务
    - `GET /api/v1/tasks` — 列表查询（按角色过滤）
    - `GET /api/v1/tasks/{id}` — 详情
    - `PUT /api/v1/tasks/{id}` — 编辑任务
    - `POST /api/v1/tasks/{id}/publish` — 管理员发布任务
    - `POST /api/v1/tasks/{id}/reject` — 管理员驳回任务
    - `POST /api/v1/tasks/{id}/convert-urgent` — 转紧急任务
    - `POST /api/v1/tasks/{id}/convert-convenient` — 转便捷任务

12. **报价 API**
    - `POST /api/v1/tasks/{id}/bids` — 工程师提交报价
    - `PUT /api/v1/tasks/{id}/bids/{bid_id}` — 修改报价
    - `GET /api/v1/tasks/{id}/bids` — 查看报价列表（PM/管理员）

13. **任务执行 API**
    - `POST /api/v1/tasks/{id}/start` — 启动任务
    - `POST /api/v1/tasks/{id}/reject` — 拒绝任务
    - `POST /api/v1/tasks/{id}/pause-request` — 申请暂停
    - `POST /api/v1/tasks/{id}/pause-approve` — 管理员审批暂停
    - `POST /api/v1/tasks/{id}/resume` — 恢复任务
    - `POST /api/v1/tasks/{id}/complete` — 标记完成
    - `POST /api/v1/tasks/{id}/reassign` — 管理员改派

14. **日报 API**
    - `POST /api/v1/daily-reports` — 提交日报
    - `GET /api/v1/daily-reports` — 列表查询（按工程师、日期筛选）
    - `GET /api/v1/daily-reports/{id}` — 日报详情

15. **星点 API**
    - `GET /api/v1/starpoints/my` — 我的星点明细
    - `GET /api/v1/starpoints/leaderboard` — 星点排行榜（管理员）
    - `POST /api/v1/starpoints/adjust` — 手动调整星点（管理员）

16. **工资 API**
    - `GET /api/v1/salaries/my` — 我的工资试算
    - `GET /api/v1/salaries` — 全员工资汇总（管理员）
    - `POST /api/v1/salaries/export` — 导出工资表（管理员）
    - `PUT /api/v1/users/{id}/salary-params` — 设置工资参数（管理员）

17. **客资 API**
    - `POST /api/v1/client-resources` — PM 录入客资
    - `GET /api/v1/client-resources` — 客资列表
    - `PUT /api/v1/users/{id}/client-resource-params` — 设置客资参数（管理员）

18. **规则配置 API**
    - `GET /api/v1/system-rules` — 规则列表
    - `POST /api/v1/system-rules` — 创建规则（管理员）
    - `PUT /api/v1/system-rules/{id}` — 更新规则（管理员）

### Scope 定义

19. 新增以下 Scope：
    - `task:read`, `task:create`, `task:update`, `task:delete`, `task:admin`
    - `bid:create`, `bid:update`
    - `report:read`, `report:create`
    - `starpoint:read`, `starpoint:admin`
    - `salary:read`, `salary:admin`
    - `client-resource:read`, `client-resource:create`
    - `rule:admin`
    - `user:admin`

### 前端模块

20. **后端 Domain 模块**
    - `domains/task/` — 任务模块（schemas, repository, router, dependencies）
    - `domains/bid/` — 报价模块
    - `domains/daily-report/` — 日报模块
    - `domains/starpoint/` — 星点模块
    - `domains/salary/` — 工资模块
    - `domains/client-resource/` — 客资模块
    - `domains/system-rule/` — 规则配置模块

21. **前端 Feature 模块**
    - `features/task/` — 任务管理（工程师/PM/管理三个视图）
    - `features/bid/` — 竞价报价
    - `features/daily-report/` — 日报填报
    - `features/starpoint/` — 星点查看
    - `features/salary/` — 工资试算
    - `features/client-resource/` — 客资管理
    - `features/dashboard/` — 数据概览

22. **前端路由结构**
    - `/engineer/` — 工程师工作台首页（指标卡 + 待办）
    - `/engineer/tasks/` — 我的任务（竞价中/待启动/进行中/已完成）
    - `/engineer/bidding/` — 竞价任务列表
    - `/engineer/reports/` — 日报填报
    - `/engineer/starpoints/` — 我的星点
    - `/engineer/salary/` — 收入试算
    - `/pm/` — PM 工作台首页
    - `/pm/tasks/` — 我发布的任务
    - `/pm/tasks/new` — 发布新任务
    - `/pm/client-resources/` — 客资管理
    - `/pm/salary/` — 收入试算
    - `/admin/` — 管理端首页（数据概览）
    - `/admin/tasks/` — 任务管理
    - `/admin/reports/` — 日报汇总
    - `/admin/starpoints/` — 星点排行榜
    - `/admin/salaries/` — 工资管理
    - `/admin/users/` — 人员管理
    - `/admin/rules/` — 规则配置

### 业务逻辑

23. **竞价中标逻辑**（ADR-0006）
    - 报价窗口 24 小时，所有工程师报完价可提前截止
    - 计算所有报价的平均值
    - 选择报价最接近平均值的工程师中标
    - 仅一人报价时直接中标
    - 无人报价或全部拒绝时进入下一轮竞价

24. **星点计算逻辑**（ADR-0002）
    - T实 ≤ 0.8 × T报：提前完成，+5 星点
    - T实 ≤ T报：按时完成，+3 星点
    - T实 ≤ 1.2 × T报：超时 ≤ 20%，-5 星点
    - T实 ≤ 1.5 × T报：超时 21-50%，-10 星点
    - T实 ≤ 2 × T报：超时 51-100%，-20 星点
    - T实 > 2 × T报：超时 > 100%，-30 星点
    - 紧急任务完成：+15 星点

25. **K 系数计算逻辑**（ADR-0003）
    - 按星点排名分组
    - 前 20%：K = 1.1
    - 中 60%：K = 1.0
    - 后 20%：K = 0.9
    - 排名相同时按 T报准确率、任务完成数排序

26. **工资计算逻辑**
    - 工程师：S下 = (S0 - P差额) × K
    - PM：S总 = S底 + S考，其中 S考 与客资增长挂钩

27. **日报联动逻辑**
    - 阶段选择"已完成"时，进度自动设为 100%
    - T实根据每日"今日投入"自动累加
    - 完成判定和预计星点仅阶段为"已完成"时显示

### 通知机制

28. 站内消息系统（ADR 需补充）
    - 任务状态变更通知（中标、被指派、被改派等）
    - 竞价结果通知
    - 日报提交提醒
    - 审批结果通知

## Testing Decisions

### 测试策略

采用单元测试 + 集成测试组合：

1. **单元测试**
   - 测试业务逻辑函数（星点计算、K系数计算、中标判定）
   - 不依赖数据库，使用 mock 数据
   - 覆盖边界条件（如 T实/T报 比例边界值）

2. **集成测试**
   - 测试 API 路由 + Repository + 数据库
   - 使用测试数据库（SQLite 内存数据库或 PostgreSQL 测试容器）
   - 覆盖完整业务流程

### 测试模块

3. **后端测试**
   - `tests/unit/test_starpoint_calculation.py` — 星点计算逻辑
   - `tests/unit/test_k_coefficient.py` — K系数计算
   - `tests/unit/test_bid_selection.py` — 中标判定逻辑
   - `tests/integration/test_task_api.py` — 任务 API
   - `tests/integration/test_bid_api.py` — 报价 API
   - `tests/integration/test_report_api.py` — 日报 API
   - `tests/integration/test_workflow.py` — 完整业务流程（竞价→执行→完成→星点→工资）

4. **前端测试**
   - 组件测试：关键交互组件
   - E2E 测试（可选）：关键用户流程

### 测试数据

5. 使用工厂函数创建测试数据
6. 测试数据库每次测试后回滚

## Out of Scope

以下内容不在本规格范围内：

1. **外部系统集成**：企业微信/钉钉/飞书通知、CRM 同步
2. **移动端应用**：仅 Web 端
3. **多语言支持**：仅中文
4. **审计日志详细报表**：仅基础操作日志
5. **自动化部署流水线**：手动部署即可
6. **高级数据分析**：BI 报表、数据导出到 Excel 分析

## Further Notes

### 技术栈确认

- 后端：FastAPI + SQLModel + PostgreSQL + Alembic
- 前端：Next.js 16 + React 19 + TanStack Query + shadcn/ui
- SDK：OpenAPI 自动生成 + React Query Hooks
- 文件存储：本地文件系统

### 开发优先级建议

1. **P0（核心流程）**：任务管理 → 竞价报价 → 任务执行 → 日报填报 → 星点计算 → 工资试算
2. **P1（管理功能）**：数据概览 → 人员管理 → 规则配置
3. **P2（增强功能）**：操作日志 → 附件管理 → 客资管理

### 待确认事项

1. PM 客资增长与 S考 的具体计算公式
2. T无责任扣罚 的触发条件和金额规则
3. 日报缺报的惩罚规则
4. 工资导出格式（CSV/Excel）