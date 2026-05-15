# User Stores 目录文档

## 目录概述

`apps/web/features/user/stores` 目录用于存放与用户功能相关的 **Zustand 状态管理 Store**。采用按功能域组织的方式，将用户相关的状态集中管理。

```
apps/web/features/user/stores/
├── auth.ts      # 用户认证状态管理
└── stores.md    # 本文档
```

---

## 核心文件说明

### [`auth.ts`](auth.ts:1) - 认证状态管理

基于 [Zustand](https://github.com/pmndrs/zustand) + [`persist`](auth.ts:2) 中间件实现的用户认证状态管理。

#### 功能特性

| 特性 | 说明 |
|------|------|
| **持久化存储** | 使用 localStorage 自动保存登录状态 |
| **自动恢复** | 刷新页面后自动恢复登录状态和 API 配置 |
| **Cookie 同步** | 自动同步 access_token 到 Cookie，供中间件读取 |
| **细粒度订阅** | 提供独立的选择器 Hooks，避免不必要的重渲染 |

#### 状态接口 ([`AuthState`](auth.ts:10))

```typescript
interface AuthState {
  // 状态
  user: UserPublic | null;        // 当前用户信息
  token: string | null;           // JWT 访问令牌
  isAuthenticated: boolean;       // 是否已认证
  isHydrated: boolean;            // 状态是否已从持久化恢复

  // 操作方法
  setUser: (user) => void;                    // 设置用户信息
  setToken: (token) => void;                  // 设置访问令牌
  setAuth: (user, token) => void;             // 设置完整认证信息
  logout: () => void;                         // 退出登录
  setHydrated: () => void;                    // 标记恢复完成
}
```

#### 使用方法

**1. 在组件中使用完整 Store：**

```typescript
import { useAuthStore } from "@/features/user/stores/auth";

function ProfilePage() {
  const { user, logout, setUser } = useAuthStore();

  return (
    <div>
      <h1>欢迎, {user?.full_name}</h1>
      <button onClick={logout}>退出登录</button>
    </div>
  );
}
```

**2. 使用选择器 Hooks（推荐，性能更优）：**

```typescript
import {
  useUser,
  useIsAuthenticated,
  useIsSuperuser,
  useIsHydrated,
} from "@/features/user/stores/auth";

function Navbar() {
  const user = useUser();                    // 仅订阅 user 变化
  const isAuthenticated = useIsAuthenticated(); // 仅订阅认证状态
  const isSuperuser = useIsSuperuser();      // 检查是否为管理员
  const isHydrated = useIsHydrated();        // 避免闪烁

  if (!isHydrated) return <Skeleton />;

  return isAuthenticated ? <UserMenu user={user} /> : <LoginButton />;
}
```

**3. 登录流程：**

```typescript
import { useAuthStore } from "@/features/user/stores/auth";

async function handleLogin(credentials) {
  const response = await api.login(credentials);

  // 一次性设置用户和令牌
  useAuthStore.getState().setAuth(response.user, response.token);

  // 自动完成：
  // - 配置 API 客户端 Authorization 头
  // - 设置 access_token Cookie
  // - 持久化到 localStorage
}
```

**4. 退出登录：**

```typescript
function handleLogout() {
  useAuthStore.getState().logout();
  // 自动完成：
  // - 清除 API 客户端配置
  // - 删除 Cookie
  // - 清除 localStorage
}
```

#### 持久化配置

```typescript
{
  name: "auth-storage",                    // localStorage 键名
  storage: createJSONStorage(() => localStorage),
  partialize: (state) => ({                // 选择持久化字段
    user: state.user,
    token: state.token,
    isAuthenticated: state.isAuthenticated,
    // isHydrated 不持久化，每次重置
  }),
  onRehydrateStorage: () => (state) => {   // 恢复后回调
    if (state?.token) {
      configureApiClient(state.token);      // 重新配置 API
      setCookie("access_token", state.token); // 恢复 Cookie
    }
    state?.setHydrated?.();                  // 标记恢复完成
  },
}
```

---

## 增量开发指南

### 添加新的 User Store

当需要添加新的用户相关状态管理时，遵循以下步骤：

**1. 创建新的 Store 文件**

```typescript
// apps/web/features/user/stores/preferences.ts
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface PreferencesState {
  theme: "light" | "dark" | "system";
  language: string;
  setTheme: (theme: PreferencesState["theme"]) => void;
  setLanguage: (lang: string) => void;
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      theme: "system",
      language: "zh-CN",
      setTheme: (theme) => set({ theme }),
      setLanguage: (language) => set({ language }),
    }),
    {
      name: "user-preferences",
    }
  )
);

// 导出选择器
export const useTheme = () =>
  usePreferencesStore((state) => state.theme);
export const useLanguage = () =>
  usePreferencesStore((state) => state.language);
```

**2. 更新目录索引（可选）**

如果创建了多个 Store，可以添加 `index.ts` 统一导出：

```typescript
// apps/web/features/user/stores/index.ts
export { useAuthStore, useUser, useIsAuthenticated } from "./auth";
export { usePreferencesStore, useTheme, useLanguage } from "./preferences";
```

**3. 更新本文档**

在本文档中添加新 Store 的说明和使用方法。

### Store 设计规范

1. **命名规范**
   - Store 文件: `[功能].ts` (如 `auth.ts`, `preferences.ts`)
   - Store Hook: `use[功能]Store` (如 `useAuthStore`)
   - 选择器 Hook: `use[状态名]` (如 `useUser`, `useTheme`)

2. **接口定义**
   - 始终定义明确的 State 接口
   - 区分 State（状态）和 Actions（操作方法）
   - 使用 JSDoc 注释说明每个字段和方法

3. **持久化策略**
   - 敏感信息（如 token）需要评估是否持久化
   - 使用 `partialize` 选择需要持久化的字段
   - 大型数据考虑使用 IndexedDB 替代 localStorage

4. **性能优化**
   - 为常用状态提供独立的选择器 Hooks
   - 避免在组件中订阅整个 Store
   - 使用 `onRehydrateStorage` 处理恢复后的副作用

### 与中间件集成

认证 Store 与 [`middleware.ts`](apps/web/middleware.ts:1) 的协作：

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   middleware.ts │────▶│   Cookie     │◀────│    auth.ts      │
│  (服务端检查)    │     │ access_token │     │  (客户端管理)    │
└─────────────────┘     └──────────────┘     └─────────────────┘
```

- **服务端**: 中间件读取 Cookie 判断登录状态，保护路由
- **客户端**: Store 管理状态，自动同步 Cookie 和 API 配置

---

## 依赖说明

| 依赖 | 用途 |
|------|------|
| `zustand` | 状态管理核心库 |
| `zustand/middleware` | persist 持久化中间件 |
| `@repo/sdk` | 用户类型定义 (`UserPublic`) |
| `@/src/lib/api-sdk` | API 客户端配置 |

---

## 相关文件

- [`apps/web/middleware.ts`](apps/web/middleware.ts:1) - 路由保护中间件
- [`apps/web/app/page.tsx`](apps/web/app/page.tsx:1) - 首页（使用认证状态）
- [`packages/sdk/src/api/types.gen.ts`](packages/sdk/src/api/types.gen.ts:1) - 用户类型定义
