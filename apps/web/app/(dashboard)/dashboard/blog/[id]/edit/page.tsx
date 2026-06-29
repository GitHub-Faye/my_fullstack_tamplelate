"use client";

import { useParams } from "next/navigation";
import { PostEditor } from "@/features/blog/client";
import { usePostDetail } from "@/features/blog/api";
import { Skeleton } from "@/components/ui/skeleton";

export default function EditPostPage() {
  const params = useParams<{ id: string }>();
  const postId = params.id;

  // Note: we need to find the post by slug first, then get it by ID
  // Since we're storing postId from the URL, we directly pass it to PostEditor
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">编辑文章</h1>
      <EditPostForm postId={postId} />
    </div>
  );
}

function EditPostForm({ postId }: { postId: string }) {
  // For editing, we load the post by navigating via its slug
  // But since this is admin, we could load directly by ID
  const { data: post, isLoading } = usePostDetail(postId);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-3/4" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!post) {
    return <p className="text-muted-foreground">文章不存在。</p>;
  }

  return <PostEditor initial={post} submitLabel="保存修改" postId={postId} />;
}