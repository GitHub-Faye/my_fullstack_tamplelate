"use client";

import { useRouter } from "next/navigation";
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
import { Textarea } from "@/components/ui/textarea";

import {
  itemCreateSchema,
  itemUpdateSchema,
  type ItemCreateInput,
  type ItemUpdateInput,
} from "../schemas/item";
import { useCreateItem, useUpdateItem } from "../api/client/queries";
import type { ItemPublic } from "@repo/sdk";

interface ItemFormProps {
  item?: ItemPublic;
  mode: "create" | "edit";
}

export function ItemForm({ item, mode }: ItemFormProps) {
  const router = useRouter();
  const createMutation = useCreateItem();
  const updateMutation = useUpdateItem();

  const isPending = createMutation.isPending || updateMutation.isPending;

  const form = useForm<ItemCreateInput | ItemUpdateInput>({
    resolver: zodResolver(mode === "create" ? itemCreateSchema : itemUpdateSchema),
    defaultValues: {
      title: item?.title || "",
      description: item?.description || "",
    },
  });

  async function onSubmit(data: ItemCreateInput | ItemUpdateInput) {
    try {
      if (mode === "create") {
        await createMutation.mutateAsync(data as ItemCreateInput);
        router.push("/dashboard/items");
      } else if (item) {
        await updateMutation.mutateAsync({
          itemId: item.id,
          data: data as ItemUpdateInput,
        });
        router.push("/dashboard/items");
      }
    } catch {
      // Error is handled by the mutation
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="title"
          render={({ field }) => (
            <FormItem>
              <FormLabel>标题</FormLabel>
              <FormControl>
                <Input placeholder="输入物品标题" {...field} value={field.value || ""} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>描述</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="输入物品描述（可选）"
                  className="min-h-[100px]"
                  {...field}
                  value={field.value || ""}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex gap-4">
          <Button type="submit" disabled={isPending}>
            {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {mode === "create" ? "创建" : "保存"}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push("/dashboard/items")}
            disabled={isPending}
          >
            取消
          </Button>
        </div>
      </form>
    </Form>
  );
}
