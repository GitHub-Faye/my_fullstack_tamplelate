"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useArchives } from "../api";
import type { ArchiveEntry } from "@repo/sdk";

export function ArchiveList() {
  const { data, isLoading } = useArchives();

  if (isLoading) {
    return (
      <div className="space-y-6">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-40 w-full" />
        ))}
      </div>
    );
  }

  const archives = data?.archives ?? [];

  if (archives.length === 0) {
    return <p className="text-muted-foreground">暂无归档文章。</p>;
  }

  return (
    <div className="space-y-10">
      {archives.map((entry: ArchiveEntry) => (
        <section key={`${entry.year}-${entry.month}`}>
          <h2 className="text-xl font-medium border-b border-border pb-2">
            {entry.year} 年 {String(entry.month).padStart(2, "0")} 月
          </h2>
          <ul className="mt-4 space-y-2" style={{ listStyleType: "square" }}>
            {entry.posts.map((p) => (
              <li key={p.slug} className="ml-5">
                <span className="text-muted-foreground text-sm mr-2">
                  {p.published_at
                    ? new Date(p.published_at).toLocaleDateString("zh-CN")
                    : ""}
                </span>
                <span className="mx-1 text-muted-foreground">»</span>
                <Link
                  href={`/blog/posts/${p.slug}`}
                  className="hover:underline"
                >
                  {p.title}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}