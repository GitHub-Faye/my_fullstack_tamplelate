import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { UserPublic } from "@repo/sdk";
import { configureApiClient } from "@/lib/api-sdk";

/**
 * 认证状态接口
 * 定义了用户认证相关的状态和操作方法
 */
interface AuthState {
  // ==================== 状态 (State) ====================
  /** 当前登录用户信息 */
  user: UserPublic | null;
  /** 访问令牌 (JWT Token) */
  token: string | null;
  /** 是否已认证 */
  isAuthenticated: boolean;
  /** 状态是否已从持久化存储恢复完成 */
  isHydrated: boolean;

  // ==================== 操作方法 (Actions) ====================
  /** 设置用户信息 */
  setUser: (user: UserPublic | null) => void;
  /** 设置访问令牌 */
  setToken: (token: string | null) => void;
  /** 同时设置用户和令牌（登录成功时调用） */
  setAuth: (user: UserPublic, token: string) => void;
  /** 退出登录，清除所有认证状态 */
  logout: () => void;
  /** 标记状态已恢复完成 */
  setHydrated: () => void;
}

/**
 * 设置 Cookie 的辅助函数
 * 用于在客户端设置/删除 access_token，供中间件读取
 *
 * @param name - Cookie 名称
 * @param value - Cookie 值，传入 null 表示删除
 * @param days - Cookie 有效期（天），默认 7 天
 */
function setCookie(name: string, value: string | null, days: number = 7) {
  // 服务端渲染时跳过
  if (typeof document === "undefined") return;

  if (value === null) {
    // 删除 Cookie：设置过期时间为过去
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
  } else {
    // 设置 Cookie：计算过期时间并编码值
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/;`;
  }
}

/**
 * 认证状态管理 Store
 * 使用 Zustand + persist 中间件实现持久化存储
 *
 * 特性：
 * - 自动同步到 localStorage
 * - 刷新页面后自动恢复登录状态
 * - 自动配置 API 客户端和 Cookie
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // ==================== 初始状态 ====================
      user: null,
      token: null,
      isAuthenticated: false,
      isHydrated: false,

      /**
       * 仅设置用户信息
       * 用于更新用户资料等场景
       */
      setUser: (user) => {
        set({ user });
      },

      /**
       * 设置访问令牌
       * 同时配置 API 客户端和 Cookie
       */
      setToken: (token) => {
        configureApiClient(token);
        setCookie("access_token", token);
        set({ token, isAuthenticated: !!token });
      },

      /**
       * 设置完整的认证信息
       * 登录成功后调用，同时设置用户和令牌
       */
      setAuth: (user, token) => {
        configureApiClient(token);
        setCookie("access_token", token);
        set({ user, token, isAuthenticated: true });
      },

      /**
       * 退出登录
       * 清除所有认证状态、Cookie 和 API 配置
       */
      logout: () => {
        configureApiClient(null);
        setCookie("access_token", null);
        set({ user: null, token: null, isAuthenticated: false });
      },

      /**
       * 标记状态已从持久化存储恢复
       * 用于避免页面加载时的闪烁问题
       */
      setHydrated: () => {
        set({ isHydrated: true });
      },
    }),

    
    {
      // 持久化存储的键名
      name: "auth-storage",
      // 使用 localStorage 作为存储介质
      storage: createJSONStorage(() => localStorage),

      /**
       * 选择需要持久化的字段
       * 不持久化 isHydrated，每次重新加载时重置
       */
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),

      /**
       * 从持久化存储恢复后的回调
       * 重新配置 API 客户端和 Cookie
       */
      onRehydrateStorage: () => (state) => {
        if (state?.token) {
          configureApiClient(state.token);
          setCookie("access_token", state.token);
        }
        // 标记恢复完成
        state?.setHydrated?.();
      },
    }
  )
);

// ==================== 选择器 Hooks (Selectors) ====================
// 使用细粒度的选择器优化性能，避免不必要的重渲染

/** 获取当前用户信息 */
export const useUser = () => useAuthStore((state) => state.user);

/** 获取访问令牌 */
export const useToken = () => useAuthStore((state) => state.token);

/** 获取是否已认证 */
export const useIsAuthenticated = () =>
  useAuthStore((state) => state.isAuthenticated);

/** 获取是否为超级管理员 */
export const useIsSuperuser = () =>
  useAuthStore((state) => state.user?.is_superuser ?? false);

/** 获取状态是否已恢复完成 */
export const useIsHydrated = () => useAuthStore((state) => state.isHydrated);
