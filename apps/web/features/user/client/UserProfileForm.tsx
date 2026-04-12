"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { userUpdateMeSchema, type UserUpdateMeFormData } from "../schemas";
import { useUpdateCurrentUser } from "../api/client/queries";
import type { UserPublic } from "@repo/sdk";

interface UserProfileFormProps {
  user: UserPublic;
}

export function UserProfileForm({ user }: UserProfileFormProps) {
  const updateMutation = useUpdateCurrentUser();

  const form = useForm<UserUpdateMeFormData>({
    resolver: zodResolver(userUpdateMeSchema),
    defaultValues: {
      email: user.email || "",
      fullName: user.full_name || "",
    },
  });

  async function onSubmit(data: UserUpdateMeFormData) {
    try {
      // Only send changed fields
      const updateData: UserUpdateMeFormData = {};
      if (data.email && data.email !== user.email) {
        updateData.email = data.email;
      }
      if (data.fullName !== user.full_name) {
        updateData.fullName = data.fullName || undefined;
      }

      if (Object.keys(updateData).length === 0) {
        return;
      }

      await updateMutation.mutateAsync(updateData);
    } catch {
      // Error is handled by the mutation
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>个人资料</CardTitle>
        <CardDescription>更新您的个人信息</CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>邮箱</FormLabel>
                  <FormControl>
                    <Input
                      type="email"
                      placeholder="name@example.com"
                      {...field}
                      disabled={updateMutation.isPending}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="fullName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>姓名</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="请输入您的姓名"
                      {...field}
                      value={field.value || ""}
                      disabled={updateMutation.isPending}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex gap-4">
              <Button
                type="submit"
                disabled={updateMutation.isPending || !form.formState.isDirty}
              >
                {updateMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    保存中...
                  </>
                ) : (
                  "保存更改"
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => form.reset()}
                disabled={updateMutation.isPending || !form.formState.isDirty}
              >
                重置
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
