"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, RotateCcw, Plus } from "lucide-react";

/**
 * 管理员角色管理页面
 */
export default function AdminRolesPage() {
  const [search] = useState("");

  const roles = [
    { name: "管理员", code: "ADMIN", permissions: "全量", status: "正常" },
    { name: "市场产品PM", code: "PM", permissions: "PM工作台/操作日志", status: "正常" },
    { name: "工程师", code: "ENGINEER", permissions: "工程师工作台/操作日志", status: "正常" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">角色管理</h1>
        <p className="text-muted-foreground">管理系统中的角色和权限</p>
      </div>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4 flex-wrap">
            <Button variant="default" size="sm" disabled>
              <Plus className="mr-1 h-4 w-4" />
              新增角色
            </Button>
            <div className="flex items-center gap-2">
              <label className="text-sm">角色名称</label>
              <Input className="w-[160px]" placeholder="管理员 / PM / 工程师" value={search} disabled />
            </div>
            <Button variant="outline" size="sm" disabled>
              <Search className="mr-1 h-4 w-4" />
              搜索
            </Button>
            <Button variant="ghost" size="sm" disabled>
              <RotateCcw className="mr-1 h-4 w-4" />
              重置
            </Button>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>角色管理</CardTitle></CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-muted-foreground">
                  <th className="text-left py-3 px-4">角色</th>
                  <th className="text-left py-3 px-4">权限字符</th>
                  <th className="text-left py-3 px-4">菜单权限</th>
                  <th className="text-left py-3 px-4">状态</th>
                  <th className="text-right py-3 px-4">操作</th>
                </tr>
              </thead>
              <tbody>
                {roles.map((role) => (
                  <tr key={role.code} className="border-b last:border-0">
                    <td className="py-3 px-4 font-medium">{role.name}</td>
                    <td className="py-3 px-4">{role.code}</td>
                    <td className="py-3 px-4">{role.permissions}</td>
                    <td className="py-3 px-4"><span className="px-2 py-1 text-xs rounded-full bg-primary/10 text-primary">{role.status}</span></td>
                    <td className="py-3 px-4 text-right"><Button variant="link" size="sm" disabled>修改权限</Button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}