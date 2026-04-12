import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ItemTable } from "@/features/item/client";
import { Plus } from "lucide-react";
import Link from "next/link";

export const metadata = {
  title: "物品管理",
  description: "管理您的物品",
};

export default function ItemsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">物品管理</h1>
          <p className="text-muted-foreground">管理您的所有物品</p>
        </div>
        <Button asChild>
          <Link href="/dashboard/items/new">
            <Plus className="mr-2 h-4 w-4" />
            新建物品
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>物品列表</CardTitle>
          <CardDescription>查看和管理您的物品</CardDescription>
        </CardHeader>
        <CardContent>
          <ItemTable />
        </CardContent>
      </Card>
    </div>
  );
}
