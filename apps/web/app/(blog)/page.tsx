"use client";

import { PostList } from "@/features/blog/client";
import { usePosts } from "@/features/blog/api";
import type { PostPublic } from "@repo/sdk";

export default function BlogHomePage() {
  const { data, isLoading } = usePosts({
    pagination: { page: 1, page_size: 10 },
  });

  const posts = (data?.data ?? []) as PostPublic[];
  const featured = posts[0];

  return (
    <div>
      {/* First post as featured */}
      {featured && (
        <article className="pb-10 border-b border-border">
          <h1 className="text-3xl md:text-4xl font-serif leading-snug">
            {featured.title}
          </h1>
          {featured.category && (
            <p className="mt-4 text-sm text-muted-foreground">
              分类：{" "}
              <a
                href={`/blog/category/${featured.category.slug}`}
                className="text-accent hover:underline"
              >
                {featured.category.name}
              </a>
            </p>
          )}
          <p className="mt-6 leading-loose">{featured.excerpt}</p>
          <p className="mt-6">
            <a
              href={`/blog/posts/${featured.slug}`}
              className="text-green-600 hover:underline"
            >
              继续阅读全文 »
            </a>
          </p>
          <p className="mt-6 text-xs text-muted-foreground">
            {featured.published_at
              ? new Date(featured.published_at).toLocaleDateString("zh-CN")
              : ""}{" "}
            08:01 |{" "}
            <a href={`/blog/posts/${featured.slug}#comments`}>
              留言（{featured.comments_count ?? 0}）
            </a>
          </p>
        </article>
      )}

      {/* Latest posts list */}
      <section className="mt-10">
        <h2 className="text-lg font-medium pb-2 border-b border-border">
          最新文章
        </h2>
        <PostList posts={posts.slice(1)} isLoading={isLoading} />
      </section>
    </div>
  );
}