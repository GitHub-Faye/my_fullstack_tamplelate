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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import { useAdminCreateUser, useAdminUpdateUser } from "../api/client/admin-queries";
import { ROLE_OPTIONS, EMPLOYMENT_STATUS_OPTIONS } from "@/lib/utils";
import type { UserAdminDetail } from "@repo/sdk";

interface UserFormProps {
  user?: UserAdminDetail;
  mode: "create" | "edit";
}

export function UserForm({ user, mode }: UserFormProps) {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const isEdit = mode === "edit";

  const createMutation = useAdminCreateUser();
  const updateMutation = useAdminUpdateUser();

  const schema = isEdit ? userUpdateSchema : userCreateSchema;

  const form = useForm<UserCreateFormData | UserUpdateFormData>({
    resolver: zodResolver(schema),
    defaultValues: isEdit
      ? {
          email: user?.email || "",
          fullName: user?.full_name || "",
          isActive: user?.is_active ?? true,
          isSuperuser: user?.is_superuser ?? false,
          password: "",
          phone: user?.phone || "",
          department: user?.department || "",
          hireDate: user?.hire_date || "",
          employmentStatus: user?.employment_status || undefined,
          role: user?.role || undefined,
          S0: user?.S0 ?? undefined,
          H0: user?.H0 ?? undefined,
          TMonthlyPlan: user?.T_monthly_plan ?? undefined,
          SBase: user?.S_base ?? undefined,
          SAssess: user?.S_assess ?? undefined,
          RBase: user?.R_base ?? undefined,
          RAssess: user?.R_assess ?? undefined,
          baselineClientCount: user?.baseline_client_count ?? undefined,
        }
      : {
          email: "",
          password: "",
          fullName: "",
          isActive: true,
          isSuperuser: false,
          phone: "",
          department: "",
          hireDate: "",
          role: "engineer",
        },
  });

  const selectedRole = form.watch("role");

  async function onSubmit(data: UserCreateFormData | UserUpdateFormData) {
    try {
      if (isEdit && user) {
        // 构建 body，只传有值的字段
        const body: Record<string, unknown> = {
          email: data.email || null,
          full_name: data.fullName || null,
          is_active: data.isActive ?? null,
          phone: data.phone || null,
          department: data.department || null,
          hire_date: data.hireDate || null,
          employment_status: data.employmentStatus || null,
          role: data.role || null,
          S0: data.S0 ?? null,
          H0: data.H0 ?? null,
          T_monthly_plan: data.TMonthlyPlan ?? null,
          S_base: data.SBase ?? null,
          S_assess: data.SAssess ?? null,
          R_base: data.RBase ?? null,
          R_assess: data.RAssess ?? null,
          baseline_client_count: data.baselineClientCount ?? null,
        };
        // 编辑时如果填了密码则一起提交
        if (data.password) {
          body.password = data.password;
        }
        await updateMutation.mutateAsync({
          path: { user_id: user.id },
          body,
          url: '/v1/admin/users/{user_id}',
        });
        router.push("/admin/users");
      } else {
        const createData = data as UserCreateFormData;
        await createMutation.mutateAsync({
          body: {
            email: createData.email!,
            password: createData.password,
            full_name: createData.fullName || undefined,
            is_active: createData.isActive,
            phone: createData.phone || undefined,
            department: createData.department || undefined,
            hire_date: createData.hireDate || undefined,
            employment_status: createData.employmentStatus || undefined,
            role: createData.role || "engineer",
            S0: createData.S0,
            H0: createData.H0,
            T_monthly_plan: createData.TMonthlyPlan,
            S_base: createData.SBase,
            S_assess: createData.SAssess,
            R_base: createData.RBase,
            R_assess: createData.RAssess,
            baseline_client_count: createData.baselineClientCount,
          },
          url: '/v1/admin/users',
        });
        router.push("/admin/users");
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
          {isEdit ? "修改用户信息和权限" : "创建一个新用户账户"}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* 基本信息 */}
            <div className="text-sm font-semibold text-muted-foreground border-b pb-2">基本信息</div>

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>邮箱</FormLabel>
                    <FormControl>
                      <Input type="email" placeholder="name@example.com" {...field} disabled={isPending} />
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
                      <Input placeholder="请输入用户姓名" {...field} value={field.value || ""} disabled={isPending} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="phone"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>手机号</FormLabel>
                    <FormControl>
                      <Input placeholder="请输入手机号" {...field} value={field.value || ""} disabled={isPending} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="department"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>部门</FormLabel>
                    <FormControl>
                      <Input placeholder="请输入部门" {...field} value={field.value || ""} disabled={isPending} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="role"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>角色</FormLabel>
                    <Select
                      value={field.value}
                      onValueChange={field.onChange}
                      disabled={isPending}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="选择角色" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {ROLE_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="employmentStatus"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>在岗状态</FormLabel>
                    <Select
                      value={field.value}
                      onValueChange={field.onChange}
                      disabled={isPending}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="选择状态" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {EMPLOYMENT_STATUS_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="hireDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>入职日期</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} value={field.value || ""} disabled={isPending} />
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
                    <FormLabel>{isEdit ? "新密码（留空则不修改）" : "密码"}</FormLabel>
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
                          {showPassword ? <EyeOff className="h-4 w-4 text-muted-foreground" /> : <Eye className="h-4 w-4 text-muted-foreground" />}
                        </Button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* 账号设置 */}
            <div className="text-sm font-semibold text-muted-foreground border-b pb-2 pt-2">账号设置</div>

            <div className="flex gap-8">
              <FormField
                control={form.control}
                name="isActive"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                    <FormControl>
                      <Checkbox checked={field.value} onCheckedChange={field.onChange} disabled={isPending} />
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
                      <Checkbox checked={field.value} onCheckedChange={field.onChange} disabled={isPending} />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                      <FormLabel className="font-normal">超级管理员</FormLabel>
                    </div>
                  </FormItem>
                )}
              />
            </div>

            {/* 工资字段 - 工程师 */}
            {(!selectedRole || selectedRole === "engineer") && (
              <>
                <div className="text-sm font-semibold text-muted-foreground border-b pb-2 pt-2">工资字段（工程师）</div>
                <div className="grid grid-cols-3 gap-4">
                  <FormField
                    control={form.control}
                    name="S0"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>S0（工资基数）</FormLabel>
                        <FormControl>
                          <Input type="number" min={0} step={0.01} placeholder="0" {...field}
                            onChange={(e) => field.onChange(e.target.value ? parseFloat(e.target.value) : undefined)}
                            value={field.value ?? ""} disabled={isPending} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="H0"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>H0（基准时薪）</FormLabel>
                        <FormControl>
                          <Input type="number" min={0} step={0.01} placeholder="0" {...field}
                            onChange={(e) => field.onChange(e.target.value ? parseFloat(e.target.value) : undefined)}
                            value={field.value ?? ""} disabled={isPending} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="TMonthlyPlan"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>T月计划（工时）</FormLabel>
                        <FormControl>
                          <Input type="number" min={0} step={0.5} placeholder="0" {...field}
                            onChange={(e) => field.onChange(e.target.value ? parseFloat(e.target.value) : undefined)}
                            value={field.value ?? ""} disabled={isPending} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </>
            )}

            {/* 工资字段 - PM */}
            {selectedRole === "pm" && (
              <>
                <div className="text-sm font-semibold text-muted-foreground border-b pb-2 pt-2">工资字段（PM）</div>
                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="SBase"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>S底（底薪）</FormLabel>
                        <FormControl>
                          <Input type="number" min={0} step={0.01} placeholder="0" {...field}
                            onChange={(e) => field.onChange(e.target.value ? parseFloat(e.target.value) : undefined)}
                            value={field.value ?? ""} disabled={isPending} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="SAssess"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>S考（考核部分）</FormLabel>
                        <FormControl>
                          <Input type="number" min={0} step={0.01} placeholder="0" {...field}
                            onChange={(e) => field.onChange(e.target.value ? parseFloat(e.target.value) : undefined)}
                            value={field.value ?? ""} disabled={isPending} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <FormField
                    control={form.control}
                    name="RBase"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>R底（底薪比例）</FormLabel>
                        <FormControl>
                          <Input type="number" min={0} max={1} step={0.01} placeholder="0" {...field}
                            onChange={(e) => field.onChange(e.target.value ? parseFloat(e.target.value) : undefined)}
                            value={field.value ?? ""} disabled={isPending} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="RAssess"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>R考（考核比例）</FormLabel>
                        <FormControl>
                          <Input type="number" min={0} max={1} step={0.01} placeholder="0" {...field}
                            onChange={(e) => field.onChange(e.target.value ? parseFloat(e.target.value) : undefined)}
                            value={field.value ?? ""} disabled={isPending} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="baselineClientCount"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>L基（基准客资数）</FormLabel>
                        <FormControl>
                          <Input type="number" min={0} step={1} placeholder="0" {...field}
                            onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : undefined)}
                            value={field.value ?? ""} disabled={isPending} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </>
            )}

            <div className="flex gap-4 pt-4">
              <Button type="submit" disabled={isPending}>
                {isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {isEdit ? "保存中..." : "创建中..."}
                  </>
                ) : isEdit ? "保存更改" : "创建用户"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.push("/admin/users")} disabled={isPending}>
                取消
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}