"use client";

import { useParams } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ItemForm } from "@/features/item/client/ItemForm";
import { useItem } from "@/features/item/api/client/queries";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function EditItemPage() {
  const params = useParams();
  const itemId = params.id as string;
  const { data: item, isLoading } = useItem(itemId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!item) {
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

      <div>
        <h1 className="text-3xl font-bold">编辑物品</h1>
        <p className="text-muted-foreground">修改物品信息</p>
      </div>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>物品信息</CardTitle>
          <CardDescription>更新物品的基本信息</CardDescription>
        </CardHeader>
        <CardContent>
          <ItemForm item={item} mode="edit" />
        </CardContent>
      </Card>
    </div>
  );
}
