"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
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
  roleCreateSchema,
  roleUpdateSchema,
  AVAILABLE_SCOPES,
  type RoleCreateInput,
  type RoleUpdateInput,
} from "../schemas/role";
import { useCreateRole, useUpdateRole } from "../api/client/queries";
import type { RolePublic } from "@repo/sdk";
import { BUILTIN_ROLES } from "@repo/contracts/scopes";

interface RoleFormProps {
  role?: RolePublic;
  mode: "create" | "edit";
}

export function RoleForm({ role, mode }: RoleFormProps) {
  const router = useRouter();
  const createMutation = useCreateRole();
  const updateMutation = useUpdateRole();

  const isPending = createMutation.isPending || updateMutation.isPending;
  const isEdit = mode === "edit";
  const isBuiltin = isEdit && role ? (BUILTIN_ROLES as readonly string[]).includes(role.name) : false;

  const form = useForm<RoleCreateInput | RoleUpdateInput>({
    resolver: zodResolver(isEdit ? roleUpdateSchema : roleCreateSchema),
    defaultValues: {
      name: role?.name || "",
      scopes: role?.scopes ?? [],
    },
  });

  async function onSubmit(data: RoleCreateInput | RoleUpdateInput) {
    try {
      if (isEdit && role) {
        await updateMutation.mutateAsync({
          roleId: role.id,
          data: { name: data.name, scopes: data.scopes },
        });
        router.push("/dashboard/roles");
      } else {
        await createMutation.mutateAsync({
          name: data.name ?? "",
          scopes: data.scopes ?? [],
        });
        router.push("/dashboard/roles");
      }
    } catch {
      // Error is handled by the mutation
    }
  }

  const selectedScopes = form.watch("scopes") ?? [];

  function toggleScope(scope: string) {
    const current = (form.getValues("scopes") ?? []) as string[];
    const next = current.includes(scope)
      ? current.filter((s) => s !== scope)
      : [...current, scope];
    form.setValue("scopes", next, { shouldValidate: true });
  }

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>{isEdit ? "编辑角色" : "创建角色"}</CardTitle>
        <CardDescription>
          {isEdit
            ? "修改角色名称和权限范围"
            : "创建一个新角色并分配权限范围"}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>角色名</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="如：order_manager"
                      {...field}
                      disabled={isPending || isBuiltin}
                    />
                  </FormControl>
                  <FormDescription>
                    {isBuiltin
                      ? "系统预置角色不可修改名称"
                      : "唯一标识，创建后影响引用此角色的用户"}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="scopes"
              render={() => (
                <FormItem>
                  <FormLabel>权限 Scope</FormLabel>
                  <FormDescription>
                    {isEdit
                      ? "保存时会整体替换角色的权限集合"
                      : "勾选该角色可拥有的权限范围"}
                  </FormDescription>
                  <div className="grid grid-cols-1 gap-2 pt-2">
                    {AVAILABLE_SCOPES.map((scope) => (
                      <label
                        key={scope}
                        className="flex items-center space-x-3 rounded-md border p-3 cursor-pointer hover:bg-muted/50 transition-colors"
                      >
                        <Checkbox
                          checked={selectedScopes.includes(scope)}
                          onCheckedChange={() => toggleScope(scope)}
                          disabled={isPending || isBuiltin}
                        />
                        <div className="space-y-1">
                          <p className="text-sm font-mono leading-none">{scope}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex gap-4">
              <Button type="submit" disabled={isPending}>
                {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isEdit ? "保存" : "创建"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => router.push("/dashboard/roles")}
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
