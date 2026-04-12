import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ItemForm } from "@/features/item/client/ItemForm";

export const metadata = {
  title: "新建物品",
  description: "创建新物品",
};

export default function NewItemPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">新建物品</h1>
        <p className="text-muted-foreground">创建一个新的物品</p>
      </div>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>物品信息</CardTitle>
          <CardDescription>填写物品的基本信息</CardDescription>
        </CardHeader>
        <CardContent>
          <ItemForm mode="create" />
        </CardContent>
      </Card>
    </div>
  );
}
