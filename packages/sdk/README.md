# SDK Package

本包包含从 OpenAPI 规范自动生成的 API SDK，使用 `@hey-api/openapi-ts` 生成。

## 配置

SDK 通过 [`openapi-ts.config.local.ts`](./openapi-ts.config.local.ts) 配置生成：

```typescript
import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: 'http://localhost:8000/openapi.json',
  output: {
    path: './src/api',
    module: {
        extension: '.js',
      },
  },
  
  plugins: [
      '@hey-api/typescript',
      '@hey-api/sdk',
      'zod',
      '@hey-api/client-fetch',
      '@tanstack/react-query',
    ],
});
```

## 插件说明

### 1. `@hey-api/typescript`
**作用**：从 OpenAPI 模式生成 TypeScript 类型定义。

**生成文件**：[`src/api/types.gen.ts`](./src/api/types.gen.ts)
- 包含所有 TypeScript 接口和类型：
  - 请求体类型（如 `BodyLoginAccessTokenV1LoginAccessTokenPost`）
  - 响应类型（如 `ItemPublic`、`UserPublic`）
  - 错误类型（如 `HttpValidationError`）
  - 所有 API 操作的数据传输对象
  - 客户端选项类型（`ClientOptions`）

### 2. `@hey-api/sdk`
**作用**：生成调用 API 端点的主要 SDK 函数。

**生成文件**：[`src/api/sdk.gen.ts`](./src/api/sdk.gen.ts)
- 包含每个端点的类型化 API 客户端函数：
  - `loginAccessTokenV1LoginAccessTokenPost` - OAuth2 令牌登录
  - `testTokenV1LoginTestTokenPost` - 测试访问令牌
  - `readUsersV1UsersGet` - 获取所有用户
  - `createUserV1UsersPost` - 创建新用户
  - `readUserByIdV1UsersUserIdGet` - 根据 ID 获取用户
  - `updateUserV1UsersUserIdPatch` - 更新用户
  - `deleteUserV1UsersUserIdDelete` - 删除用户
  - `readItemsV1ItemsGet` - 获取所有项目
  - `createItemV1ItemsPost` - 创建新项目
  - `readItemV1ItemsItemIdGet` - 根据 ID 获取项目
  - `updateItemV1ItemsItemIdPut` - 更新项目
  - `deleteItemV1ItemsItemIdDelete` - 删除项目
  - 等等...

### 3. `zod`
**作用**：从 OpenAPI 模式生成 Zod 验证模式，用于运行时类型验证。

**生成文件**：[`src/api/zod.gen.ts`](./src/api/zod.gen.ts)
- 包含所有数据类型的 Zod 模式：
  - `zBodyLoginAccessTokenV1LoginAccessTokenPost` - 登录表单验证
  - `zItemCreate` - 项目创建验证
  - `zItemPublic` - 项目公开数据验证
  - `zItemUpdate` - 项目更新验证
  - `zUserCreate` - 用户创建验证
  - `zUserPublic` - 用户公开数据验证
  - 等等...
- 使用这些模式在发送到 API 之前验证数据

### 4. `@hey-api/client-fetch`
**作用**：使用原生 Fetch API 生成 HTTP 客户端配置和工具函数。

**生成文件**：
- [`src/api/client.gen.ts`](./src/api/client.gen.ts) - 主客户端实例和配置
- [`src/api/client/`](./src/api/client/) 目录包含：
  - `client.gen.ts` - 客户端创建和配置函数
  - `types.gen.ts` - 客户端特定类型
  - `utils.gen.ts` - 请求工具函数
- [`src/api/core/`](./src/api/core/) 目录包含：
  - `auth.gen.ts` - 认证工具
  - `bodySerializer.gen.ts` - 请求体序列化
  - `params.gen.ts` - URL 参数处理
  - `pathSerializer.gen.ts` - 路径参数序列化
  - `queryKeySerializer.gen.ts` - 查询参数序列化
  - `serverSentEvents.gen.ts` - SSE 处理
  - `types.gen.ts` - 核心类型定义
  - `utils.gen.ts` - 核心工具函数

### 5. `@tanstack/react-query`
**作用**：生成 React Query hooks 和选项，用于数据获取、缓存和状态管理。

**生成文件**：[`src/api/@tanstack/react-query.gen.ts`](./src/api/@tanstack/react-query.gen.ts)
- 包含 React Query 集成：
  - GET 端点的查询选项函数（如 `readUsersV1UsersGetOptions`）
  - POST/PUT/PATCH/DELETE 端点的变更选项函数（如 `loginAccessTokenV1LoginAccessTokenPostMutation`）
  - 分页端点的无限查询选项
  - 用于缓存的查询键生成
  - 与 SDK 函数集成的类型安全 hooks

## 插件关系与数据流

插件以分层架构协同工作：

```
┌─────────────────────────────────────────────────────────────────┐
│  第 5 层：React Query 集成 (@tanstack/react-query)              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • 用 React Query hooks 包装 SDK 函数                     │  │
│  │  • 提供缓存、重新获取和状态管理                           │  │
│  │  • 依赖：sdk.gen.ts、types.gen.ts、client.gen.ts         │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  第 4 层：SDK 函数 (@hey-api/sdk)                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • 高级 API 端点函数                                      │  │
│  │  • 使用 types.gen.ts 中的类型确保类型安全                 │  │
│  │  • 使用 client.gen.ts 中的客户端发送 HTTP 请求            │  │
│  │  • 依赖：types.gen.ts、client.gen.ts                     │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  第 3 层：HTTP 客户端 (@hey-api/client-fetch)                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Fetch API 包装器，带配置                               │  │
│  │  • 处理请求/响应序列化                                    │  │
│  │  • 管理认证和请求头                                       │  │
│  │  • 依赖：types.gen.ts 中的类型                           │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  第 2 层：类型定义 (@hey-api/typescript)                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • 从 OpenAPI 模式生成的 TypeScript 接口                  │  │
│  │  • 被所有其他层用于类型安全                               │  │
│  │  • 基础层 - 无依赖                                        │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  第 1 层：验证模式 (zod)                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • 运行时验证模式                                         │  │
│  │  • 镜像 types.gen.ts 的结构                               │  │
│  │  • 可选 - 独立用于表单验证                                │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 依赖链

```
OpenAPI 模式（输入）
    │
    ├──► @hey-api/typescript ──► types.gen.ts
    │                              │
    │                              ├──► @hey-api/client-fetch ──► client.gen.ts + client/ + core/
    │                              │                              │
    │                              │                              └──► @hey-api/sdk ──► sdk.gen.ts
    │                              │                                                     │
    │                              │                                                     └──► @tanstack/react-query ──► react-query.gen.ts
    │                              │
    └──► zod ──► zod.gen.ts（独立，镜像类型）
```

### 它们如何协同工作

1. **`@hey-api/typescript`** 是**基础层** - 从 OpenAPI 生成所有其他插件依赖的类型

2. **`@hey-api/client-fetch`** 建立在类型之上 - 创建知道如何使用这些类型发出请求的 HTTP 客户端

3. **`@hey-api/sdk`** 使用两者 - 创建使用客户端进行 HTTP 调用的类型化 API 函数

4. **`@tanstack/react-query`** 包装 SDK - 创建调用 SDK 函数并带有缓存功能的 React Query hooks

5. **`zod`** 并行运行 - 生成镜像类型的验证模式，用于运行时验证（表单等）

### 导入关系

```typescript
// sdk.gen.ts 从 types.gen.ts 和 client.gen.ts 导入
import { type Client, type Options } from './client/index.js';
import type { LoginAccessTokenData, LoginAccessTokenResponse } from './types.gen.js';

// react-query.gen.ts 从 sdk.gen.ts、types.gen.ts 和 client.gen.ts 导入
import { loginAccessTokenV1LoginAccessTokenPost, type Options } from '../sdk.gen.js';
import type { LoginAccessTokenData, LoginAccessTokenResponse } from '../types.gen.js';
import { client } from '../client.gen.js';

// zod.gen.ts 是独立的，但镜像 types.gen.ts 的结构
import * as z from 'zod';
export const zItemCreate = z.object({ ... }); // 镜像 ItemCreate 类型
```

## 生成的目录结构

```
src/api/
├── index.ts                    # 所有生成文件的主导出
├── sdk.gen.ts                  # API 端点函数 (@hey-api/sdk)
├── types.gen.ts                # TypeScript 类型定义 (@hey-api/typescript)
├── zod.gen.ts                  # Zod 验证模式 (zod 插件)
├── client.gen.ts               # HTTP 客户端实例 (@hey-api/client-fetch)
├── client/                     # 客户端工具 (@hey-api/client-fetch)
│   ├── client.gen.ts           # 客户端创建函数
│   ├── index.ts                # 客户端导出
│   ├── types.gen.ts            # 客户端类型
│   └── utils.gen.ts            # 客户端工具函数
├── core/                       # 核心客户端功能 (@hey-api/client-fetch)
│   ├── auth.gen.ts             # 认证
│   ├── bodySerializer.gen.ts   # 请求体序列化
│   ├── params.gen.ts           # 参数处理
│   ├── pathSerializer.gen.ts   # 路径序列化
│   ├── queryKeySerializer.gen.ts # 查询键处理
│   ├── serverSentEvents.gen.ts # SSE 支持
│   ├── types.gen.ts            # 核心类型
│   └── utils.gen.ts            # 核心工具函数
└── @tanstack/
    └── react-query.gen.ts      # React Query hooks (@tanstack/react-query)
```

## 使用方式

### 基础 SDK 使用

```typescript
import { client } from '@repo/sdk/api/client.gen';
import { loginAccessTokenV1LoginAccessTokenPost } from '@repo/sdk/api/sdk.gen';

// 配置客户端基础 URL
client.setConfig({
  baseUrl: 'http://localhost:8000'
});

// 调用 API 端点
const response = await loginAccessTokenV1LoginAccessTokenPost({
  body: {
    username: 'user@example.com',
    password: 'password'
  }
});
```

### 配合 React Query 使用

```typescript
import { useMutation, useQuery } from '@tanstack/react-query';
import { loginAccessTokenV1LoginAccessTokenPostMutation } from '@repo/sdk/api/@tanstack/react-query.gen';
import { readUsersV1UsersGetOptions } from '@repo/sdk/api/@tanstack/react-query.gen';

// 查询数据
const { data: users } = useQuery(readUsersV1UsersGetOptions());

// 变更数据（创建/更新）
const loginMutation = useMutation(loginAccessTokenV1LoginAccessTokenPostMutation());
loginMutation.mutate({ body: { username, password } });
```

### 配合 Zod 验证使用

```typescript
import { zItemCreate } from '@repo/sdk/api/zod.gen';

// 发送到 API 前验证数据
const result = zItemCreate.safeParse({
  title: '新项目',
  description: '项目描述'
});

if (result.success) {
  // 数据有效，可以安全地发送到 API
  await createItemV1ItemsPost({ body: result.data });
}
```

## 重新生成 SDK

要从 OpenAPI 规范重新生成 SDK：

```bash
# 确保 API 在本地运行
pnpm --filter @repo/sdk generate:local
```

或手动执行：

```bash
cd packages/sdk
npx @hey-api/openapi-ts -c openapi-ts.config.local.ts
```
