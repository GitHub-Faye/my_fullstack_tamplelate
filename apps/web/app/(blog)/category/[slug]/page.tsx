"use client";

import { useParams } from "next/navigation";
import { PostList } from "@/features/blog/client";
import { useCategoryPosts } from "@/features/blog/api";
import type { PostPublic } from "@repo/sdk";

export default function CategoryPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;

  const { data, isLoading } = useCategoryPosts(slug, {
    page: 1,
    page_size: 20,
  });

  const posts = (data?.data ?? []) as PostPublic[];

  return (
    <div>
      <h1 className="text-3xl font-serif">分类：{slug}</h1>
      <div className="mt-8">
        <PostList posts={posts} isLoading={isLoading} />
      </div>
    </div>
  );
}