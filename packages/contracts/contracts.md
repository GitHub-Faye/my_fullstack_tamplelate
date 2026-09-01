# @repo/contracts - 前后端共享业务契约层

## 概述

`@repo/contracts` 与 `@repo/sdk` 共同组成前后端共享的"业务契约层"：

- **@repo/sdk**: OpenAPI 自动生成的接口契约（类型、API 客户端、Zod Schema）
- **@repo/contracts**: 手动维护的业务语义契约（错误码、权限 Scope、分页协议、业务常量）

## 目录结构

```
packages/contracts/
├── src/
│   ├── index.ts      # 统一导出
│   ├── errors.ts     # 错误码定义
│   ├── scopes.ts     # 权限 Scope 定义
│   ├── pagination.ts # 分页协议
│   └── constants.ts  # 业务常量
├── package.json
└── tsconfig.json
```

## 模块说明

### errors.ts - 错误码

与后端 `apps/api/app/core/errors.py` 保持同步的错误码定义。

```typescript
import { ErrorCode, BusinessError, ERROR_STATUS_MAP } from '@repo/contracts/errors';

// 使用错误码
try {
  await api.createUser(data);
} catch (error) {
  if (error.code === ErrorCode.USER_EMAIL_ALREADY_EXISTS) {
    // 处理邮箱已存在
  }
}
```

### scopes.ts - 权限 Scope

与后端 `apps/api/app/core/scopes.py` 保持逐字同步的权限定义
（`UserScope` / `RoleScope` 分别对应后端 user / role 两个业务域）。

```typescript
import { UserScope, hasScope, DEFAULT_ROLE_SCOPES } from '@repo/contracts/scopes';

// 检查权限
if (hasScope(userScopes, UserScope.READ)) {
  // 允许读取用户
}

// 检查角色权限
if (hasScope(userScopes, RoleScope.READ)) {
  // 允许读取角色
}

// 获取角色权限
const adminScopes = DEFAULT_ROLE_SCOPES['admin'];
```

### pagination.ts - 分页协议

统一分页请求/响应格式。

```typescript
import { PaginatedResponse, PaginationParams, buildPaginatedResponse } from '@repo/contracts/pagination';

// 分页响应类型
type UsersResponse = PaginatedResponse<User>;

// 构建分页响应
const response = buildPaginatedResponse(data, totalCount, page, pageSize);
```

### constants.ts - 业务常量

前端 UI 依赖的稳定业务常量。

```typescript
import { UserStatus, UserRole, StorageKeys, PAGE_SIZE_OPTIONS } from '@repo/contracts/constants';

// 使用常量
localStorage.setItem(StorageKeys.ACCESS_TOKEN, token);
```

## 与后端的同步

当修改以下后端文件时，需要同步更新 contracts：

| 后端文件 | Contracts 文件 | 说明 |
|---------|---------------|------|
| `apps/api/app/core/errors.py` | `src/errors.ts` | 错误码枚举 |
| `apps/api/app/core/scopes.py` | `src/scopes.ts` | 权限 Scope |
| `apps/api/app/core/schemas.py` | `src/pagination.ts` | 分页协议 |

> 同步由 `packages/contracts/test/consistency.test.ts` 自动校验：枚举字符串集合、状态码映射、错误消息 key、BUILTIN_ROLES 与 DEFAULT_ROLE_SCOPES 均逐字比对。任一不一致该测试立即失败。

## 错误协议统一约定

- 错误响应：`{ detail: string, code: ErrorCode, data?: Record<string, unknown> }`
- HTTP 状态码由 `ERROR_STATUS_MAP` 给出：
  - 400：业务请求错误（`SYSTEM_BAD_REQUEST` / 鉴权失败等）
  - 401：令牌无效 / 过期
  - 403：权限 / scope 不足 / 预置角色保护 / 超管自删
  - 404：资源不存在
  - 409：资源冲突（邮箱已存在 / 角色名冲突）
  - **422**：Pydantic 校验错误（`SYSTEM_VALIDATION_ERROR`）
  - 429：限流
  - 500：内部错误
- 前端展示层（toast 等）允许使用本地化文案（中文）；后端 `detail` 与 contracts 文本保持英文作为协议常量。

## 分页约定

- 请求参数：`page`（≥1）+ `page_size`（1..100）
- 默认值来自 `DEFAULT_PAGINATION = { page: 1, page_size: 20 }`
- 前端列表/查询默认值必须消费 `DEFAULT_PAGINATION`，禁止硬编码 `page_size: 10` 等。

## responses.py 双入口约定

- `apps/api/app/core/responses.py`：分页工具函数（`paginated_fields` / `total_pages`），与 `core/schemas.py:PaginatedResponse` 配套
- `apps/api/app/domains/*/responses.py`：DTO 组装函数（`user_public` / `roles_public`），把 DB 模型 + 权限 scope 拼成响应 DTO

两者职责不同、命名相同；新增领域时按此约定落位。

## 使用示例

```typescript
import {
  ErrorCode,
  UserScope,
  RoleScope,
  PaginatedResponse,
  buildPaginatedResponse
} from '@repo/contracts';

// 错误处理
import { BusinessError } from '@repo/contracts/errors';

// 权限检查
import { hasScope, DEFAULT_ROLE_SCOPES } from '@repo/contracts/scopes';

// 分页
import { PaginationParams, buildPaginatedResponse } from '@repo/contracts/pagination';
```

## 职责边界

| 契约类型 | 归属 | 说明 |
|---------|------|------|
| API 接口类型 | `@repo/sdk` | OpenAPI 自动生成 |
| 数据模型类型 | `@repo/sdk` | OpenAPI 自动生成 |
| 验证规则 | `@repo/sdk` | Zod Schema 自动生成 |
| 错误码 | `@repo/contracts` | 手动维护 |
| 权限 Scope | `@repo/contracts` | 手动维护 |
| 分页协议 | `@repo/contracts` | 手动维护 |
| 业务常量 | `@repo/contracts` | 手动维护 |
    