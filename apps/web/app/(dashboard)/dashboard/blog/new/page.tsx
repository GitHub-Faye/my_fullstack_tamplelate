"use client";

import { PostEditor } from "@/features/blog/client";

export default function NewPostPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">发布新文章</h1>
      <PostEditor submitLabel="发布" />
    </div>
  );
}