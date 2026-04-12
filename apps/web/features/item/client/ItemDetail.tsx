"use client";

import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/src/lib/utils";
import Link from "next/link";
import { ArrowLeft, Package, Loader2 } from "lucide-react";
import { useItem } from "../api/client/queries";

interface ItemDetailProps {
  itemId: string;
}

/**
 * ItemDetail Client Component
 * Fetches and displays a single item's details
 */
export function ItemDetail({ itemId }: ItemDetailProps) {
  const router = useRouter();
  const { data: item, isLoading, error } = useItem(itemId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error || !item) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="sm" asChild>
            <Link href="/dashboard/items">
              <ArrowLeft className="mr-2 h-4 w-4" />
              返回列表
            </Link>
          </Button>
        </div>
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold">物品不存在</h2>
          <p className="text-muted-foreground">该物品可能已被删除或您没有访问权限</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" asChild>
          <Link href="/dashboard/items">
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回列表
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Package className="h-6 w-6 text-muted-foreground" />
            <div>
              <CardTitle>{item.title}</CardTitle>
              <CardDescription>物品详情</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4">
            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">描述</span>
              <span className="text-sm">
                {item.description || "暂无描述"}
              </span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">创建时间</span>
              <span className="text-sm">{formatDate(item.created_at)}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">物品 ID</span>
              <span className="text-sm font-mono text-xs">{item.id}</span>
            </div>
          </div>

          <div className="flex gap-2 pt-4">
            <Button asChild>
              <Link href={`/dashboard/items/${item.id}/edit`}>编辑物品</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
