"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Eye, EyeOff, Loader2 } from "lucide-react";

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
import { Checkbox } from "@/components/ui/checkbox";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import {
  userCreateSchema,
  userUpdateSchema,
  type UserCreateFormData,
  type UserUpdateFormData,
} from "../schemas";
import { useCreateUser, useUpdateUser } from "../api/client/queries";
import type { UserPublic } from "@repo/sdk";

interface UserFormProps {
  user?: UserPublic;
  mode: "create" | "edit";
}

export function UserForm({ user, mode }: UserFormProps) {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const isEdit = mode === "edit";

  const createMutation = useCreateUser();
  const updateMutation = useUpdateUser();

  // Use any to avoid complex type issues with conditional schemas
  const schema = isEdit ? userUpdateSchema : userCreateSchema;

  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: isEdit
      ? {
          email: user?.email || "",
          fullName: user?.full_name || "",
          isActive: user?.is_active ?? true,
          isSuperuser: user?.is_superuser ?? false,
          password: "",
        }
      : {
          email: "",
          username: "",
          password: "",
          fullName: "",
          isActive: true,
          isSuperuser: false,
        },
  });

  async function onSubmit(data: unknown) {
    try {
      if (isEdit && user) {
        const formData = data as UserUpdateFormData;
        // Filter out empty values for update
        const updateData: UserUpdateFormData = {};
        if (formData.email) updateData.email = formData.email;
        if (formData.fullName !== undefined) updateData.fullName = formData.fullName || null;
        if (formData.isActive !== undefined) updateData.isActive = formData.isActive;
        if (formData.isSuperuser !== undefined) updateData.isSuperuser = formData.isSuperuser;
        if (formData.password) updateData.password = formData.password;

        await updateMutation.mutateAsync({
          userId: user.id,
          data: updateData,
        });
        router.push("/dashboard/admin");
      } else {
        const formData = data as UserCreateFormData;
        await createMutation.mutateAsync({
          email: formData.email,
          username: formData.username,
          password: formData.password,
          full_name: formData.fullName || undefined,
          is_active: formData.isActive,
          is_superuser: formData.isSuperuser,
        });
        router.push("/dashboard/admin");
      }
    } catch {
      // Error is handled by the mutation
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>{isEdit ? "编辑用户" : "创建用户"}</CardTitle>
        <CardDescription>
          {isEdit
            ? "修改用户信息和权限"
            : "创建一个新用户账户"}
        </CardDescription>
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
                      disabled={isPending}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {!isEdit && (
              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>用户名</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="3-50个字符，字母数字下划线"
                        {...field}
                        disabled={isPending}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            <FormField
              control={form.control}
              name="fullName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>姓名</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="请输入用户姓名"
                      {...field}
                      value={field.value || ""}
                      disabled={isPending}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>
                    {isEdit ? "新密码（留空则不修改）" : "密码"}
                  </FormLabel>
                  <FormControl>
                    <div className="relative">
                      <Input
                        type={showPassword ? "text" : "password"}
                        placeholder={isEdit ? "可选" : "至少8个字符"}
                        {...field}
                        disabled={isPending}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowPassword(!showPassword)}
                        disabled={isPending}
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <Eye className="h-4 w-4 text-muted-foreground" />
                        )}
                      </Button>
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex gap-8">
              <FormField
                control={form.control}
                name="isActive"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                        disabled={isPending}
                      />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                      <FormLabel className="font-normal">激活账户</FormLabel>
                    </div>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="isSuperuser"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                        disabled={isPending}
                      />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                      <FormLabel className="font-normal">超级管理员</FormLabel>
                    </div>
                  </FormItem>
                )}
              />
            </div>

            <div className="flex gap-4 pt-4">
              <Button type="submit" disabled={isPending}>
                {isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {isEdit ? "保存中..." : "创建中..."}
                  </>
                ) : isEdit ? (
                  "保存更改"
                ) : (
                  "创建用户"
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => router.push("/dashboard/admin")}
                disabled={isPending}
              >
                取消
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
