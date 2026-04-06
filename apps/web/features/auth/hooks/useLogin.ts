'use client';

import { useMutation } from '@tanstack/react-query';
import { login } from '../api/login';
import { useAuthStore } from '@/src/stores/auth';

export function useLogin() {
  const { setToken, setUser } = useAuthStore();

  return useMutation({
    mutationFn: login,
    onSuccess: (data) => {
      setToken(data.access_token);
      // Fetch user details and set to store
      // For simplicity, we'll assume the token is enough for now
    },
  });
}
