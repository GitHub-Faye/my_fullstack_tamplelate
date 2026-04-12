import { notFound } from "next/navigation";
import { getItemById } from "../api/server/queries";
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
import { ArrowLeft, Package } from "lucide-react";

interface ItemDetailProps {
  itemId: string;
}

/**
 * ItemDetail Server Component
 * Fetches and displays a single item's details
 */
export async function ItemDetail({ itemId }: ItemDetailProps) {
  const item = await getItemById(itemId);

  if (!item) {
    notFound();
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
