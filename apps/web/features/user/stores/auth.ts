import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { UserPublic } from "@repo/sdk";
import { configureApiClient } from "@/src/lib/api-sdk";

interface AuthState {
  // State
  user: UserPublic | null;
  token: string | null;
  isAuthenticated: boolean;
  isHydrated: boolean;

  // Actions
  setUser: (user: UserPublic | null) => void;
  setToken: (token: string | null) => void;
  setAuth: (user: UserPublic, token: string) => void;
  logout: () => void;
  setHydrated: () => void;
}

// Helper to set cookie for middleware
function setCookie(name: string, value: string | null, days: number = 7) {
  if (typeof document === "undefined") return;

  if (value === null) {
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
  } else {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/;`;
  }
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      isHydrated: false,

      // Set user only
      setUser: (user) => {
        set({ user });
      },

      // Set token and configure API client
      setToken: (token) => {
        configureApiClient(token);
        setCookie("access_token", token);
        set({ token, isAuthenticated: !!token });
      },

      // Set both user and token
      setAuth: (user, token) => {
        configureApiClient(token);
        setCookie("access_token", token);
        set({ user, token, isAuthenticated: true });
      },

      // Clear auth state
      logout: () => {
        configureApiClient(null);
        setCookie("access_token", null);
        set({ user: null, token: null, isAuthenticated: false });
      },

      // Mark store as hydrated
      setHydrated: () => {
        set({ isHydrated: true });
      },
    }),
    {
      name: "auth-storage",
      storage: createJSONStorage(() => localStorage),
      // Only persist these fields
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
      // Reconfigure API client and cookie on rehydrate
      onRehydrateStorage: () => (state) => {
        if (state?.token) {
          configureApiClient(state.token);
          setCookie("access_token", state.token);
        }
        // Mark as hydrated
        state?.setHydrated?.();
      },
    }
  )
);

// Selector hooks for better performance
export const useUser = () => useAuthStore((state) => state.user);
export const useToken = () => useAuthStore((state) => state.token);
export const useIsAuthenticated = () =>
  useAuthStore((state) => state.isAuthenticated);
export const useIsSuperuser = () =>
  useAuthStore((state) => state.user?.is_superuser ?? false);
export const useIsHydrated = () => useAuthStore((state) => state.isHydrated);
