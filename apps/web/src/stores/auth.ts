import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserPublic } from '@repo/sdk';

type AuthStore = {
  user: UserPublic | null;
  token: string | null;
  setUser: (user: UserPublic) => void;
  setToken: (token: string) => void;
  logout: () => void;
};

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      setUser: (user) => set({ user }),
      setToken: (token) => set({ token }),
      logout: () => set({ user: null, token: null }),
    }),
    {
      name: 'auth-store',
    }
  )
);
