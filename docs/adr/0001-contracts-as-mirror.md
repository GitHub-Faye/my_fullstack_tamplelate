# ADR 0001: Contracts 作为后端核心契约的镜像

## 状态
Accepted

## 背景

本项目采用 "API First + 共享契约" 的前后端架构：
- 后端：FastAPI + SQLModel + Pydantic v2
- 前端：Next.js 16 + React 19 + TanStack Query + Zustand
- SDK：`@repo/sdk` 由 `@hey-api/openapi-ts` 从后端 OpenAPI 规范自动生成
- Contracts：`@repo/contracts` 手动维护的业务语义契约（错误码、Scope、分页、常量）

两套契约层分工：
| 契约层 | 来源 | 维护方式 | 内容 |
|-------|------|---------|------|
| `@repo/sdk` | 后端 OpenAPI | 自动生成（`pnpm generate`） | 请求/响应 DTO、API 客户端、Zod schema |
| `@repo/contracts` | 后端 `core/` | 手动镜像同步 | `ErrorCode`、`UserScope/RoleScope`、`PaginationParams`、业务常量 |

## 决策

### 1. contracts 为后端 Python `core/` 模块的**手动镜像**，不可自动生成
- `errors.py` → `errors.ts`（错误码枚举、状态码映射、默认消息）
- `scopes.py` → `scopes.ts`（Scope 字符串、预置角色、角色默认 Scope）
- `schemas.py` → `pagination.ts`（分页请求/响应结构、默认值、校验函数）

任何一边修改字符串集合而忘记同步另一边，会破坏前后端语义一致性。

### 2. SDK 生成物**禁止手改**
- `packages/sdk/src/api/**` 由 `openapi-ts` 生成
- 改协议必须回到后端 Python（修改 Pydantic/SQLModel → `pnpm generate` → diff 审查）
- `openapi-ts.config.ts` 为基线配置，`openapi-ts.config.local.ts` 仅作本地覆盖

### 3. 统一错误响应协议
```
{
  "detail": "string | ErrorDetail[]",  // 422 为数组，其余为字符串
  "code": "ERROR_CODE",
  "data"?: Record<string, unknown>     // 可选扩展（如 SYSTEM_VALIDATION_ERROR 的 errors 列表）
}
```
- HTTP 状态码由 `ERROR_STATUS_MAP` 定义：
  - 400 `SYSTEM_BAD_REQUEST` / 鉴权失败等
  - 401 令牌无效/过期
  - 403 权限/scope 不足、预置角色保护、超管自删、最后超管保护
  - 404 资源不存在
  - 409 冲突
  - **422 `SYSTEM_VALIDATION_ERROR`（Pydantic 校验）**
  - 429 限流
  - 500 内部错误

### 4. 统一分页协议
- 请求：`PaginationParams { page: ≥1, page_size: 1..100 }`
- 默认值 `DEFAULT_PAGINATION = { page: 1, page_size: 20 }`（后端同步 `PaginationParams` 的默认字段）
- 响应：`PaginatedResponse<T> { data, count, page, page_size, total_pages }`
- 前端所有列表查询默认值必须消费 `DEFAULT_PAGINATION`，禁止硬编码 `page_size: 10`

### 5. 契约一致性由测试守护
- `packages/contracts/test/consistency.test.ts`：
  - 枚举字符串集合逐字比对
  - `ERROR_STATUS_MAP` / `DEFAULT_ERROR_MESSAGES` key 集合比对
  - `BUILTIN_ROLES` / `DEFAULT_ROLE_SCOPES` 逐字比对
- CI 必须包含 `pnpm test`（会跑 contracts + web + api 三包测试）

### 6. responses.py 双入口约定（避免命名冲突）
| 文件 | 职责 |
|------|------|
| `apps/api/app/core/responses.py` | 分页工具函数（`paginated_fields`、`total_pages`）|
| `apps/api/app/domains/*/responses.py` | DTO 组装函数（`user_public`、`roles_public`）——把 DB 模型 + 权限 scope 拼成响应 DTO |

新增业务域时按此约定落位。

## 后果

### 正面
- 前后端错误码/Scope/分页逐字一致，消除手动同步遗漏
- `pnpm test` 一条命令覆盖契约层、前端、后端全链路
- SDK 生成物不可变，避免“生成后手改导致再次生成冲突”的问题

### 负面
- 修改后端 `errors.py`/`scopes.py` 后必须同步 `contracts`（显性成本）
- `contracts` 新增字段需同时更新 Python 侧与 TS 侧（双写）
- 依赖 `consistency.test.ts` 的正则提取 Python 源码，Python 重构需同步测试

## 替代方案评估

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| 完全自动生成（OpenAPI 包含 scopes/errors） | 零手动同步 | OpenAPI 不擅长表达业务语义常量（Scope 列表、预置角色、默认消息） | 不采纳 |
| 仅用 SDK（不维护 contracts） | 减少一层 | SDK 只含 DTO，无 Scope/错误码/分页常量，前端仍需手写 | 不采纳 |
| 现有双契约 + 手动同步 + 测试守护 | 语义清晰、类型安全、测试可控 | 双写成本 | **采纳** |

## 关联
- P0-3 修复 `openapi-ts.config.ts` 空文件
- P1-7 新增 `consistency.test.ts`
- P2-12 本 ADR