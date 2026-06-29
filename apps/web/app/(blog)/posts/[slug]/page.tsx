"use client";

import { useParams } from "next/navigation";
import { PostDetail } from "@/features/blog/client";
import { CommentSection } from "@/features/blog/client";
import { usePostDetail, useComments } from "@/features/blog/api";
import type { CommentPublic } from "@repo/sdk";

export default function PostPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;

  const { data: post, isLoading: postLoading } = usePostDetail(slug);
  const {
    data: commentsData,
    isLoading: commentsLoading,
    refetch: refreshComments,
  } = useComments(slug, { page: 1, page_size: 50 });

  const comments = (commentsData?.data ?? []) as CommentPublic[];

  if (postLoading) {
    return (
      <div className="space-y-4">
        <div className="h-10 w-3/4 bg-muted animate-pulse rounded" />
        <div className="h-4 w-1/4 bg-muted animate-pulse rounded" />
        <div className="h-64 w-full bg-muted animate-pulse rounded" />
      </div>
    );
  }

  if (!post) {
    return (
      <div>
        <p className="text-muted-foreground">文章不存在。</p>
      </div>
    );
  }

  return (
    <div>
      <PostDetail post={post} />
      <CommentSection
        postSlug={slug}
        comments={comments}
        isLoading={commentsLoading}
        onRefresh={refreshComments}
      />
    </div>
  );
}