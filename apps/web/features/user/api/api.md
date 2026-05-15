# User API 模块文档

## 目录

- [技术栈](#技术栈)
- [架构设计](#架构设计)
- [与后端服务器沟通](#与后端服务器沟通)
- [增量开发指南](#增量开发指南)

---

## 技术栈

### 核心依赖

| 技术 | 版本 | 用途 |
|------|------|------|
| [Next.js](apps/web/package.json:35) | 16.2.0 | React 框架，支持 SSR/SSG |
| [React](apps/web/package.json:37) | ^19.2.0 | UI 库 |
| [TypeScript](apps/web/package.json:61) | 5.9.2 | 类型安全 |
| [@tanstack/react-query](apps/web/package.json:29) | ^5.96.2 | 服务端状态管理、数据获取 |
| [@repo/sdk](apps/web/package.json:26) | workspace:^ | 自动生成的 API 客户端 |
| [Zustand](apps/web/package.json:43) | ^5.0.12 | 客户端状态管理 |
| [Zod](apps/web/package.json:42) | ^4.3.6 | 运行时类型验证 |

### SDK 生成工具

| 工具 | 用途 |
|------|------|
| [@hey-api/openapi-ts](packages/sdk/package.json:27) | 从 OpenAPI 规范生成 TypeScript SDK |
| [@hey-api/client-fetch](packages/sdk/package.json:22) | HTTP 客户端底层 |
| [@hey-api/sdk](packages/sdk/openapi-ts.config.local.ts:16) | SDK 生成插件 |
| [@hey-api/typescript](packages/sdk/openapi-ts.config.local.ts:14) | TypeScript 类型生成 |
| [zod](packages/sdk/openapi-ts.config.local.ts:15) | Schema 验证生成 |
| [@tanstack/react-query](packages/sdk/openapi-ts.config.local.ts:17) | React Query hooks 生成 |

---

## 架构设计

### 目录结构

```
apps/web/features/user/api/
├── api.md              # 本文档
├── index.ts            # 统一导出客户端和服务端 API
├── client/
│   ├── index.ts        # 导出客户端 queries
│   └── queries.ts      # React Query hooks (useQuery, useMutation)
└── server/
    ├── index.ts        # 导出服务端 queries
    └── queries.ts      # Server Actions (Server Components 使用)
```

### 双模式架构

本模块采用 **Client/Server 双模式** 设计，支持 Next.js App Router 的混合渲染策略：

#### 1. Client 端 ([`client/queries.ts`](apps/web/features/user/api/client/queries.ts:1))

- 使用 `"use client"` 指令
- 基于 [@tanstack/react-query](apps/web/features/user/api/client/queries.ts:4) 的 hooks
- 适用于交互式组件、表单提交、实时更新

**主要功能：**

| Hook | 用途 |
|------|------|
| [`useCurrentUser`](apps/web/features/user/api/client/queries.ts:72) | 获取当前登录用户信息 |
| [`useUsers`](apps/web/features/user/api/client/queries.ts:95) | 获取用户列表（管理员） |
| [`useUser`](apps/web/features/user/api/client/queries.ts:122) | 获取指定用户详情 |
| [`useLogin`](apps/web/features/user/api/client/queries.ts:152) | 用户登录 |
| [`useSignup`](apps/web/features/user/api/client/queries.ts:191) | 用户注册 |
| [`useCreateUser`](apps/web/features/user/api/client/queries.ts:212) | 创建用户（管理员） |
| [`useUpdateCurrentUser`](apps/web/features/user/api/client/queries.ts:236) | 更新当前用户信息 |
| [`useUpdatePassword`](apps/web/features/user/api/client/queries.ts:262) | 修改密码 |
| [`useUpdateUser`](apps/web/features/user/api/client/queries.ts:283) | 更新指定用户（管理员） |
| [`useDeleteCurrentUser`](apps/web/features/user/api/client/queries.ts:317) | 删除当前账户 |
| [`useDeleteUser`](apps/web/features/user/api/client/queries.ts:342) | 删除指定用户（管理员） |

#### 2. Server 端 ([`server/queries.ts`](apps/web/features/user/api/server/queries.ts:1))

- 使用 `"use server"` 指令
- 直接在 Server Components 中调用
- 适用于初始数据获取、SEO 优化

**主要功能：**

| 函数 | 用途 |
|------|------|
| [`getUsers`](apps/web/features/user/api/server/queries.ts:19) | 服务端获取用户列表 |
| [`getUserById`](apps/web/features/user/api/server/queries.ts:33) | 服务端获取用户详情 |
| [`getCurrentUser`](apps/web/features/user/api/server/queries.ts:51) | 服务端获取当前用户 |

---

## 与后端服务器沟通

### 1. SDK 生成流程

```
后端 OpenAPI Schema → @hey-api/openapi-ts → TypeScript SDK
```

**配置位置：** [`packages/sdk/openapi-ts.config.local.ts`](packages/sdk/openapi-ts.config.local.ts:1)

```typescript
export default defineConfig({
  input: 'http://localhost:8000/openapi.json',  // 后端 API 文档地址
  output: {
    path: './src/api',
    module: { extension: '.js' },
  },
  plugins: [
    '@hey-api/client-fetch',    // HTTP 客户端
    '@hey-api/typescript',      // 类型定义
    'zod',                      // 验证 Schema
    '@hey-api/sdk',             // SDK 函数
    '@tanstack/react-query',    // React Query hooks
  ],
});
```

### 2. 生成命令

```bash
# 在 packages/sdk 目录下执行
cd packages/sdk
pnpm generate:local    # 从本地后端生成 SDK
```

### 3. SDK 使用方式

#### 方式一：直接调用 SDK 函数（原始 API 调用）

直接调用 SDK 函数是最基础的使用方式，适合简单的、一次性的数据获取场景。

```typescript
import { readUserMeV1UsersMeGet, loginAccessTokenV1LoginAccessTokenPost } from "@repo/sdk";

// 获取当前用户 - 直接调用 SDK
const response = await readUserMeV1UsersMeGet({ throwOnError: true });
console.log(response.data);

// 登录 - 直接调用 SDK
const loginResponse = await loginAccessTokenV1LoginAccessTokenPost({
  body: { username: "user", password: "pass" },
  throwOnError: true,
});
```

**特点：**
- ✅ 简单直接，无额外依赖
- ✅ 适合 Server Components 和 Server Actions
- ❌ 无缓存机制，每次调用都会发起网络请求
- ❌ 需要手动处理 loading、error 状态
- ❌ 组件卸载后无法自动取消请求

#### 方式二：使用 React Query Hooks（推荐）

React Query Hooks 是对 SDK 的封装，提供了完整的状态管理和缓存机制。

```typescript
import { useCurrentUser, useLogin } from "@/features/user/api/client";

// 在组件中使用
function UserProfile() {
  // 自动管理 loading、error、data 状态
  const { data: user, isLoading, error } = useCurrentUser();
  
  // Mutation 用于修改操作
  const loginMutation = useLogin();
  
  const handleLogin = () => {
    loginMutation.mutate({ username: "user", password: "pass" });
  };
  
  if (isLoading) return <div>加载中...</div>;
  if (error) return <div>错误: {error.message}</div>;
  
  return <div>用户名: {user?.full_name}</div>;
}
```

**特点：**
- ✅ 自动缓存数据，避免重复请求
- ✅ 自动管理 loading、error、data 状态
- ✅ 支持后台自动刷新（stale-while-revalidate）
- ✅ 窗口重新聚焦时自动刷新数据（可配置）
- ✅ 组件卸载自动取消请求
- ✅ 支持乐观更新、分页、无限滚动等高级功能
- ✅ 内置开发工具（React Query Devtools）

---

### 4. 直接调用 SDK vs Query Hook 对比

| 特性 | 直接调用 SDK | React Query Hook |
|------|-------------|------------------|
| **使用场景** | Server Components、Server Actions、简单一次性调用 | Client Components、需要状态管理的场景 |
| **缓存** | ❌ 无缓存 | ✅ 自动缓存，可配置缓存策略 |
| **状态管理** | ❌ 手动管理 loading/error | ✅ 自动提供 isLoading/isError/data |
| **重复请求** | ❌ 每次调用都发起请求 | ✅ 智能去重，相同 key 只请求一次 |
| **自动刷新** | ❌ 不支持 | ✅ 支持窗口聚焦、定时刷新等 |
| **请求取消** | ❌ 需手动处理 | ✅ 组件卸载自动取消 |
| **乐观更新** | ❌ 需手动实现 | ✅ 内置支持 |
| **代码量** | 较少 | 稍多（但复用性高） |
| **学习成本** | 低 | 中等 |

**选择建议：**

| 场景 | 推荐方式 | 原因 |
|------|---------|------|
| Server Component 初始数据 | 直接调用 SDK | 服务端渲染，不需要客户端状态管理 |
| Server Action | 直接调用 SDK | 服务端执行，无 React 生命周期 |
| 表单提交后跳转 | 直接调用 SDK | 一次性操作，不需要缓存 |
| 用户资料展示 | Query Hook | 需要缓存，可能在多个组件使用 |
| 列表/表格数据 | Query Hook | 需要分页、筛选、自动刷新 |
| 频繁更新的数据 | Query Hook | 支持后台自动刷新 |
| 购物车、订单状态 | Query Hook | 需要乐观更新提升用户体验 |

**示例对比：**

```tsx
// ❌ 直接调用 SDK - 需要手动管理所有状态
"use client";
function UserProfileBad() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    
    readUserMeV1UsersMeGet({ throwOnError: true })
      .then(res => {
        if (!cancelled) setUser(res.data);
      })
      .catch(err => {
        if (!cancelled) setError(err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    
    return () => { cancelled = true; };
  }, []);
  
  if (loading) return <div>加载中...</div>;
  if (error) return <div>错误</div>;
  return <div>{user?.name}</div>;
}

// ✅ 使用 Query Hook - 简洁、功能完整
"use client";
function UserProfileGood() {
  const { data: user, isLoading, error } = useCurrentUser();
  
  if (isLoading) return <div>加载中...</div>;
  if (error) return <div>错误</div>;
  return <div>{user?.full_name}</div>;
}
```

### 5. 认证配置

SDK 客户端认证配置位于：[`apps/web/lib/api-sdk.ts`](apps/web/lib/api-sdk.ts:1)

```typescript
import { client } from "@repo/sdk";

// 配置 API 客户端认证令牌
export function configureApiClient(token: string | null) {
  if (token) {
    client.setConfig({
      auth: () => token,  // 每次请求自动添加认证头
    });
  }
}
```

### 6. 全局 Provider 配置

React Query 在 [`apps/web/components/providers.tsx`](apps/web/components/providers.tsx:1) 中配置：

```typescript
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,        // 数据缓存 1 分钟
            refetchOnWindowFocus: false, // 窗口聚焦不自动刷新
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

Provider 在根布局 [`apps/web/app/layout.tsx`](apps/web/app/layout.tsx:41) 中注入：

```tsx
<body>
  <Providers>
    {children}
    <Toaster />
  </Providers>
</body>
```

---

## 增量开发指南

### 场景 1：后端新增 API 端点

**步骤：**

1. **确保后端服务运行**并暴露 OpenAPI 文档（通常是 `/openapi.json`）

2. **重新生成 SDK**：
   ```bash
   cd packages/sdk
   pnpm generate:local
   ```

3. **检查生成的代码**：
   - 类型定义：`packages/sdk/src/api/types.gen.ts`
   - SDK 函数：`packages/sdk/src/api/sdk.gen.ts`
   - React Query hooks：`packages/sdk/src/api/@tanstack/react-query.gen.ts`

4. **在 user/api 中封装**（如果需要自定义逻辑）：
   ```typescript
   // client/queries.ts
   import { newApiFunction } from "@repo/sdk";
   
   export function useNewFeature() {
     return useQuery({
       queryKey: userKeys.newFeature(),
       queryFn: async () => {
         const response = await newApiFunction({ throwOnError: true });
         return response.data;
       },
     });
   }
   ```

### 场景 2：添加新的 Query Hook

**模板：**

```typescript
// 1. 定义 Query Key
export const userKeys = {
  all: ["users"] as const,
  lists: () => [...userKeys.all, "list"] as const,
  list: (filters: Filters) => [...userKeys.lists(), filters] as const,
  details: () => [...userKeys.all, "detail"] as const,
  detail: (id: string) => [...userKeys.details(), id] as const,
  me: () => [...userKeys.all, "me"] as const,
  // 新增 key
  newFeature: () => [...userKeys.all, "newFeature"] as const,
};

// 2. 创建 Query Hook
export function useNewFeature(
  options?: Omit<UseQueryOptions<NewFeatureResponse, Error, NewFeatureResponse>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: userKeys.newFeature(),
    queryFn: async () => {
      const response = await newApiFunction({ throwOnError: true });
      return response.data;
    },
    ...options,
  });
}
```

### 场景 3：添加新的 Mutation Hook

**模板：**

```typescript
export function useNewMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: NewMutationData) => {
      const response = await newMutationApi({
        body: data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      // 成功后刷新相关缓存
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      toast.success("操作成功");
    },
    onError: (error: Error) => {
      toast.error(error.message || "操作失败");
    },
  });
}
```

### 场景 4：添加 Server Action

**模板：**

```typescript
// server/queries.ts
"use server";

import { newApiFunction, type NewApiResponse } from "@repo/sdk";

export async function getNewFeatureData(
  params: Params
): Promise<NewApiResponse> {
  const response = await newApiFunction({
    query: params,
    throwOnError: true,
  });
  return response.data;
}
```

### 场景 5：修改现有 API 调用

**原则：**

1. **只修改封装层**，不修改生成的 SDK
2. **保持 Query Keys 一致性**，确保缓存失效逻辑正确
3. **更新类型引用**，从 `@repo/sdk` 导入最新类型

**示例：**

```typescript
// 修改前
export function useUsers(filters: OldFilters) {
  return useQuery({
    queryKey: userKeys.list(filters),
    queryFn: async () => {
      const response = await readUsersV1UsersGet({
        query: filters,
        throwOnError: true,
      });
      return response.data;
    },
  });
}

// 修改后 - 更新 filters 类型
export function useUsers(filters: NewFilters) {
  return useQuery({
    queryKey: userKeys.list(filters),  // 如果 filters 结构变化，需要更新 key 生成逻辑
    queryFn: async () => {
      const response = await readUsersV1UsersGet({
        query: filters,
        throwOnError: true,
      });
      return response.data;
    },
  });
}
```

### 开发检查清单

- [ ] 后端 API 文档已更新
- [ ] SDK 已重新生成
- [ ] 类型检查通过 (`pnpm check-types`)
- [ ] Query Keys 设计合理（支持缓存失效）
- [ ] 错误处理完善（toast 提示）
- [ ] 服务端和客户端 API 同步更新（如需要）

---

## 相关文档

- [SDK 文档](../../../packages/sdk/sdk.md) - SDK 生成和使用说明
- [Contracts 文档](../../../packages/contracts/contracts.md) - 前后端共享的业务契约
