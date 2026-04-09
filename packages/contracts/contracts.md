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
  if (error.code === ErrorCode.USER_ALREADY_EXISTS) {
    // 处理用户已存在
  }
}
```

### scopes.ts - 权限 Scope

与后端 `apps/api/app/core/scopes.py` 保持同步的权限定义。

```typescript
import { ItemScope, hasScope, DEFAULT_ROLE_SCOPES } from '@repo/contracts/scopes';

// 检查权限
if (hasScope(userScopes, ItemScope.CREATE)) {
  // 允许创建
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

## 使用示例

```typescript
import {
  ErrorCode,
  ItemScope,
  PaginatedResponse,
  UserRole,
  StorageKeys
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
    