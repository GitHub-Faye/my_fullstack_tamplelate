"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Search, RotateCcw, Plus } from "lucide-react";

/**
 * 管理员角色管理页面
 *
 * 展示系统角色列表及权限配置
 * TODO: 集成实际角色 API
 */
export default function AdminRolesPage() {
  const [search] = useState("");

  // 静态示例数据，后续接入 API 后替换
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

      {/* 筛选栏 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4 flex-wrap">
            <Button variant="default" size="sm" disabled>
              <Plus className="mr-1 h-4 w-4" />
              新增角色
            </Button>
            <div className="flex items-center gap-2">
              <label className="text-sm">角色名称</label>
              <Input
                className="w-[160px]"
                placeholder="管理员 / PM / 工程师"
                value={search}
                disabled
              />
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

      {/* 角色列表 */}
      <Card>
        <CardHeader>
          <CardTitle>角色管理</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>角色</TableHead>
                  <TableHead>权限字符</TableHead>
                  <TableHead>菜单权限</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {roles.map((role) => (
                  <TableRow key={role.code}>
                    <TableCell className="font-medium">{role.name}</TableCell>
                    <TableCell>{role.code}</TableCell>
                    <TableCell>{role.permissions}</TableCell>
                    <TableCell>
                      <Badge variant="default">{role.status}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="link" size="sm" disabled>
                        修改权限
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}