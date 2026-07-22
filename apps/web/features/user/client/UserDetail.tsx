"use client";

import { useQuery } from "@tanstack/react-query";
import { adminReadUserV1AdminUsersUserIdGet } from "@repo/sdk";
import { UserForm } from "../client/UserForm";
import { Loader2 } from "lucide-react";

interface UserDetailProps {
  userId: string;
}

/**
 * UserDetail Client Component
 * Fetches user data on the client side via admin API (full fields) and renders the client UserForm
 */
export function UserDetail({ userId }: UserDetailProps) {
  const { data: user, isLoading } = useQuery({
    queryKey: ["admin-user-detail", userId],
    queryFn: async () => {
      const response = await adminReadUserV1AdminUsersUserIdGet({
        path: { user_id: userId },
        throwOnError: true,
      });
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="text-center h-64 flex items-center justify-center">
        <p className="text-destructive">用户不存在或加载失败</p>
      </div>
    );
  }

  return <UserForm user={user} mode="edit" />;
}