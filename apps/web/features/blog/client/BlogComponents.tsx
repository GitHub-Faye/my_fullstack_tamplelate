"use client";

import Link from "next/link";
import type { PostPublic, CategoryPublic, RecentCommentPublic } from "@repo/sdk";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useRecentComments, useCategories } from "../api";

// ==================== Sidebar ====================

function SidebarBox({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card className="rounded-none border-border">
      <div className="px-4 py-2 border-b border-border text-sm font-medium text-muted-foreground">
        {title}
      </div>
      <CardContent className="p-4 text-sm">{children}</CardContent>
    </Card>
  );
}

export function Sidebar() {
  return (
    <aside className="flex flex-col gap-4 w-64 shrink-0">
      <RecentCommentsBox />
      <CategoriesBox />
    </aside>
  );
}

function RecentCommentsBox() {
  const { data: comments, isLoading } = useRecentComments({ limit: 8 });

  if (isLoading) return <Skeleton className="h-40 w-full" />;

  return (
    <SidebarBox title="最新留言">
      <ul className="space-y-2 list-disc pl-5">
        {(comments ?? []).map((c: RecentCommentPublic) => (
          <li key={c.id}>
            <Link href={`/blog/posts/${c.post_slug}`} className="hover:underline">
              {c.author_name}
            </Link>
          </li>
        ))}
        {(comments ?? []).length === 0 && (
          <li className="text-muted-foreground">暂无留言</li>
        )}
      </ul>
    </SidebarBox>
  );
}

function CategoriesBox() {
  const { data, isLoading } = useCategories({ page: 1, page_size: 100 });

  if (isLoading) return <Skeleton className="h-32 w-full" />;

  const categories = (data?.data ?? []) as CategoryPublic[];

  return (
    <SidebarBox title="分类">
      <ul className="space-y-1 list-disc pl-5">
        {categories.map((cat: CategoryPublic) => (
          <li key={cat.id}>
            <Link href={`/blog/category/${cat.slug}`} className="hover:underline">
              {cat.name} ({cat.post_count ?? 0})
            </Link>
          </li>
        ))}
        <li>
          <Link href="/blog/archives" className="hover:underline">
            归档
          </Link>
        </li>
      </ul>
    </SidebarBox>
  );
}

// ==================== BlogLayout ====================

export function BlogLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link href="/blog" className="text-xl font-serif font-bold">
            阮一峰的网络日志
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <Link href="/blog" className="hover:underline">首页</Link>
            <Link href="/blog/archives" className="hover:underline">归档</Link>
            <Link href="/login" className="hover:underline">登录</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 flex gap-8">
        <div className="flex-1 min-w-0">{children}</div>
        <Sidebar />
      </main>

      <footer className="border-t border-border py-6 text-center text-xs text-muted-foreground">
        © {new Date().getFullYear()} 阮一峰的网络日志
      </footer>
    </div>
  );
}

// ==================== PostCard ====================

export function PostCard({ post }: { post: PostPublic }) {
  return (
    <article className="pb-6 border-b border-border last:border-b-0">
      <h2 className="text-xl font-serif leading-snug">
        <Link href={`/blog/posts/${post.slug}`} className="hover:underline">
          {post.title}
        </Link>
      </h2>
      {post.category && (
        <p className="mt-2 text-xs text-muted-foreground">
          分类：{" "}
          <Link href={`/blog/category/${post.category.slug}`} className="text-accent hover:underline">
            {post.category.name}
          </Link>
        </p>
      )}
      {post.excerpt && (
        <p className="mt-3 text-sm text-muted-foreground line-clamp-2">{post.excerpt}</p>
      )}
      <p className="mt-3 text-xs text-muted-foreground flex gap-3">
        {post.published_at && <span>{new Date(post.published_at).toLocaleDateString("zh-CN")}</span>}
        <span>留言（{post.comments_count ?? 0}）</span>
      </p>
    </article>
  );
}

// ==================== PostList ====================

export function PostList({
  posts,
  isLoading,
}: {
  posts: PostPublic[];
  isLoading?: boolean;
}) {
  if (isLoading) {
    return (
      <div className="space-y-6">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
    );
  }

  if (posts.length === 0) {
    return <p className="text-muted-foreground">暂无文章。</p>;
  }

  return (
    <div className="space-y-6">
      {posts.map((p) => (
        <PostCard key={p.id} post={p} />
      ))}
    </div>
  );
}

// ==================== PostDetail ====================

export function PostDetail({
  post,
  isLoading,
}: {
  post: PostPublic & { body?: string };
  isLoading?: boolean;
}) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-3/4" />
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <article className="pb-10 border-b border-border">
      <h1 className="text-3xl md:text-4xl font-serif leading-snug">{post.title}</h1>
      {post.category && (
        <p className="mt-4 text-sm text-muted-foreground">
          分类：{" "}
          <Link href={`/blog/category/${post.category.slug}`} className="text-accent hover:underline">
            {post.category.name}
          </Link>
        </p>
      )}
      <div className="mt-6 leading-loose text-[16px] space-y-4">
        {post.body && (
          <div className="prose max-w-none" dangerouslySetInnerHTML={{ __html: post.body }} />
        )}
      </div>
      <p className="mt-8 text-xs text-muted-foreground flex gap-3">
        {post.published_at && <span>{new Date(post.published_at).toLocaleDateString("zh-CN")}</span>}
        <span>留言（{post.comments_count ?? 0}）</span>
      </p>
    </article>
  );
}