# SDK 包文档

本 SDK 包使用 [`@hey-api/openapi-ts`](https://heyapi.dev/) 从 OpenAPI 规范自动生成 TypeScript 客户端代码。

## 配置文件

配置文件位于 [`openapi-ts.config.local.ts`](./openapi-ts.config.local.ts):

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
      '@hey-api/client-fetch',
      '@hey-api/typescript',
      'zod',
      '@hey-api/sdk',
      '@tanstack/react-query',   
    ],
});
```

## 插件详解

### 1. `@hey-api/typescript`

**作用**: 从 OpenAPI Schema 生成 TypeScript 类型定义。

**生成依据**: 根据 OpenAPI 规范中的 `components.schemas` 和路径操作定义生成。

**生成内容**: 
- 数据模型类型（如 `UserPublic`, `ItemCreate`, `Token` 等）
- 请求/响应类型（如 `LoginAccessTokenV1LoginAccessTokenPostData`, `LoginAccessTokenV1LoginAccessTokenPostResponse`）
- 错误类型（如 `HttpValidationError`, `ValidationError`）
- 客户端配置类型（`ClientOptions`）

**输出文件**: [`src/api/types.gen.ts`](./src/api/types.gen.ts)

**依赖关系**: 
- 无前置依赖
- 被 `@hey-api/sdk` 和 `@tanstack/react-query` 插件依赖

---

### 2. `@hey-api/client-fetch`

**作用**: 生成基于 Fetch API 的 HTTP 客户端核心代码。

**生成依据**: 根据 OpenAPI 规范中的 `servers` 配置、`securitySchemes`（认证方案）和全局设置生成。

**生成内容**:
- HTTP 客户端实例（`createClient`, `createConfig`）
- 请求/响应处理工具
- **认证处理**（`core/auth.gen.ts`）- 根据 OpenAPI `securitySchemes` 生成 Bearer/Basic 认证逻辑
- **参数序列化**（`core/params.gen.ts`, `core/pathSerializer.gen.ts`, `core/queryKeySerializer.gen.ts`）
- **请求体序列化**（`core/bodySerializer.gen.ts`）- 支持 JSON、FormData、URLSearchParams
- **SSE 支持**（`core/serverSentEvents.gen.ts`）
- **核心类型定义**（`core/types.gen.ts`）- Client、Config、HttpMethod 等接口
- **工具函数**（`core/utils.gen.ts`）

**输出文件**:
- [`src/api/client.gen.ts`](./src/api/client.gen.ts) - 客户端实例导出
- [`src/api/client/`](./src/api/client/) 目录 - 客户端核心实现
- [`src/api/core/`](./src/api/core/) 目录 - 核心功能模块
  - `auth.gen.ts` - 认证令牌处理（Bearer/Basic）
  - `bodySerializer.gen.ts` - 请求体序列化器
  - `params.gen.ts` - 请求参数构建
  - `pathSerializer.gen.ts` - URL 路径参数序列化
  - `queryKeySerializer.gen.ts` - 查询参数序列化
  - `serverSentEvents.gen.ts` - SSE 支持
  - `types.gen.ts` - 核心类型定义（Client, Config, HttpMethod）
  - `utils.gen.ts` - 工具函数

**依赖关系**:
- 无前置依赖
- 被 `@hey-api/sdk` 和 `@tanstack/react-query` 插件依赖
- `client/index.ts` 会引用 `core/` 中的模块

---

### 3. `@hey-api/sdk`

**作用**: 生成类型安全的 SDK 函数，封装 API 调用。

**生成依据**: 根据 OpenAPI 规范中的 `paths` 定义（每个端点的 method、parameters、requestBody、responses）。

**生成内容**:
- 每个 API 端点对应的 SDK 函数（如 `loginAccessTokenV1LoginAccessTokenPost`, `readUsersV1UsersGet`, `createUserV1UsersPost` 等）
- 函数包含完整的 JSDoc 注释（从 OpenAPI description 提取）
- 类型安全的请求参数和响应处理
- 自动处理认证、Content-Type 等头部

**输出文件**: [`src/api/sdk.gen.ts`](./src/api/sdk.gen.ts)

**依赖关系**:
- **依赖 `@hey-api/typescript`**: 使用生成的类型定义（`types.gen.ts`）
- **依赖 `@hey-api/client-fetch`**: 使用生成的客户端实例（`client.gen.ts`）

**引用示例**:
```typescript
import { client } from './client.gen.js';
import { type Client, type Options as Options2, type TDataShape } from './client/index.js';
import type { CreateItemV1ItemsPostData, ... } from './types.gen.js';
```

---

### 4. `zod`

**作用**: 从 OpenAPI Schema 生成 Zod 验证模式。

**生成依据**: 根据 OpenAPI 规范中的 `components.schemas` 和路径参数定义生成。

**生成内容**:
- 每个 Schema 对应的 Zod 验证对象（如 `zUserPublic`, `zItemCreate`, `zToken` 等）
- 请求/响应验证模式（如 `zLoginAccessTokenV1LoginAccessTokenPostBody`, `zLoginAccessTokenV1LoginAccessTokenPostResponse`）
- 包含验证规则（min/max length, email, uuid, 正则等）

**输出文件**: [`src/api/zod.gen.ts`](./src/api/zod.gen.ts)

**依赖关系**:
- 无前置依赖
- 可选：可被业务代码用于运行时数据验证

**使用示例**:
```typescript
import { zUserCreate } from './zod.gen.js';

// 运行时验证
const result = zUserCreate.safeParse(userData);
```

---

### 5. `@tanstack/react-query`

**作用**: 生成与 TanStack Query (React Query) 集成的 hooks。

**生成依据**: 根据 OpenAPI 规范中的 `paths` 定义，结合已生成的 SDK 函数和类型。

**生成内容**:
- Query Options 函数（`queryOptions`, `infiniteQueryOptions`）
- Mutation Options 函数（`UseMutationOptions`）
- Query Key 生成函数
- 支持无限滚动查询（`infiniteOptions`）

**输出文件**: [`src/api/@tanstack/react-query.gen.ts`](./src/api/@tanstack/react-query.gen.ts)

**依赖关系**:
- **依赖 `@hey-api/typescript`**: 使用生成的类型定义（`types.gen.ts`）
- **依赖 `@hey-api/sdk`**: 使用生成的 SDK 函数（`sdk.gen.ts`）
- **依赖 `@hey-api/client-fetch`**: 使用客户端实例（`client.gen.ts`）

**引用示例**:
```typescript
import { type DefaultError, type InfiniteData, infiniteQueryOptions, queryOptions, type UseMutationOptions } from '@tanstack/react-query';
import { client } from '../client.gen.js';
import { createItemV1ItemsPost, ... } from '../sdk.gen.js';
import type { CreateItemV1ItemsPostData, ... } from '../types.gen.js';
```

**使用示例**:
```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import { readUsersV1UsersGetOptions, createUserV1UsersPostMutation } from './api/@tanstack/react-query.gen.js';

// Query 使用
const { data } = useQuery(readUsersV1UsersGetOptions());

// Mutation 使用
const mutation = useMutation(createUserV1UsersPostMutation());
mutation.mutate({ body: userData });
```

---

## 插件依赖关系图

```
                    OpenAPI Specification
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
@hey-api/typescript   @hey-api/client-fetch    zod
        │                   │                   │
        │                   ▼                   │
        │            @hey-api/sdk               │
        │            (依赖 types + client)      │
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                  @tanstack/react-query
                  (依赖 types + sdk + client)
```

## 文件结构

```
src/api/
├── client.gen.ts              # @hey-api/client-fetch 生成 - 客户端实例
├── types.gen.ts               # @hey-api/typescript 生成 - 类型定义
├── sdk.gen.ts                 # @hey-api/sdk 生成 - SDK 函数
├── zod.gen.ts                 # zod 插件生成 - Zod 验证模式
├── @tanstack/
│   └── react-query.gen.ts     # @tanstack/react-query 生成 - Query/Mutation hooks
├── client/                    # @hey-api/client-fetch 生成的客户端核心
│   ├── index.ts               # 统一导出（引用 core/ 模块）
│   ├── client.gen.ts          # createClient 实现
│   ├── types.gen.ts           # 客户端类型定义
│   └── utils.gen.ts           # 配置工具函数
└── core/                      # @hey-api/client-fetch 生成的核心功能模块
    ├── auth.gen.ts            # 认证处理（Bearer/Basic Token）
    ├── bodySerializer.gen.ts  # 请求体序列化（JSON/FormData/URLSearchParams）
    ├── params.gen.ts          # 请求参数构建
    ├── pathSerializer.gen.ts  # 路径参数序列化
    ├── queryKeySerializer.gen.ts  # 查询参数序列化
    ├── serverSentEvents.gen.ts    # Server-Sent Events 支持
    ├── types.gen.ts           # 核心类型（Client, Config, HttpMethod）
    └── utils.gen.ts           # 通用工具函数
```

### core/ 目录详解

`core/` 目录由 **`@hey-api/client-fetch`** 插件生成，包含 HTTP 客户端的底层核心功能：

| 文件 | 功能 | 生成依据 |
|------|------|----------|
| `auth.gen.ts` | 认证令牌处理，支持 Bearer 和 Basic 认证 | OpenAPI `securitySchemes` |
| `bodySerializer.gen.ts` | 请求体序列化器（JSON、FormData、URLSearchParams） | OpenAPI 请求体 content-type |
| `params.gen.ts` | 构建客户端请求参数 | OpenAPI 参数定义 |
| `pathSerializer.gen.ts` | URL 路径参数序列化（如 `/users/{id}`） | OpenAPI path parameters |
| `queryKeySerializer.gen.ts` | 查询参数序列化 | OpenAPI query parameters |
| `serverSentEvents.gen.ts` | SSE（Server-Sent Events）支持 | OpenAPI 响应类型 |
| `types.gen.ts` | 核心类型定义（Client, Config, HttpMethod 等） | 通用客户端类型 |
| `utils.gen.ts` | 工具函数（createConfig, mergeHeaders 等） | 通用工具 |

`client/index.ts` 会统一导出 `core/` 中的功能，供 SDK 和 React Query 插件使用。

## 使用方式

### 直接使用 SDK

```typescript
import { loginAccessTokenV1LoginAccessTokenPost, readUsersV1UsersGet } from './api/sdk.gen.js';

// 登录
const { data: token } = await loginAccessTokenV1LoginAccessTokenPost({
  body: { username: 'user', password: 'pass' }
});

// 获取用户列表
const { data: users } = await readUsersV1UsersGet();
```

### 使用 React Query

```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import { readUsersV1UsersGetOptions, createUserV1UsersPostMutation } from './api/@tanstack/react-query.gen.js';

function UsersComponent() {
  const { data, isLoading } = useQuery(readUsersV1UsersGetOptions());
  const createUser = useMutation(createUserV1UsersPostMutation());
  
  return (...);
}
```

### 使用 Zod 验证

```typescript
import { zUserCreate } from './api/zod.gen.js';

const validation = zUserCreate.safeParse(formData);
if (!validation.success) {
  console.error(validation.error);
}
```

## 重新生成代码

```bash
# 本地开发（使用本地 API）
npx @hey-api/openapi-ts -c openapi-ts.config.local.ts

# 或使用配置文件中的默认配置
npm run generate
```
