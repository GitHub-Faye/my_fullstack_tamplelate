"use client";

import { ArchiveList } from "@/features/blog/client";

export default function ArchivesPage() {
  return (
    <div>
      <h1 className="text-3xl font-serif">文章归档</h1>
      <p className="mt-2 text-sm text-muted-foreground">按年月倒序排列</p>
      <div className="mt-8">
        <ArchiveList />
      </div>
    </div>
  );
}