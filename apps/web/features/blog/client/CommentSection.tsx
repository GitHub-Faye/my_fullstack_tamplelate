"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { useCreateComment, useDeleteComment } from "../api";
import type { CommentPublic } from "@repo/sdk";
import { useIsAuthenticated, useCurrentUser } from "@/features/user";

interface CommentSectionProps {
  postSlug: string;
  comments: CommentPublic[];
  isLoading: boolean;
  onRefresh: () => void;
}

export function CommentSection({
  postSlug,
  comments,
  isLoading,
  onRefresh,
}: CommentSectionProps) {
  return (
    <section className="mt-10">
      <h2 className="text-lg font-medium pb-2 border-b border-border">
        留言（{comments.length}）
      </h2>
      <div className="mt-4 space-y-4">
        {comments.map((c) => (
          <CommentItem key={c.id} comment={c} onDelete={onRefresh} />
        ))}
        {!isLoading && comments.length === 0 && (
          <p className="text-sm text-muted-foreground">暂无留言，来说两句吧。</p>
        )}
      </div>
      <div className="mt-6">
        <CommentForm postSlug={postSlug} onSuccess={onRefresh} />
      </div>
    </section>
  );
}

function CommentItem({
  comment,
  onDelete,
}: {
  comment: CommentPublic;
  onDelete: () => void;
}) {
  const deleteComment = useDeleteComment();
  const currentUser = useCurrentUser();
  const isAuthenticated = useIsAuthenticated();

  const canDelete =
    isAuthenticated &&
    currentUser != null &&
    (currentUser.id === comment.author_id || currentUser.is_superuser);

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium">{comment.author_name}</p>
            <p className="text-xs text-muted-foreground">
              {comment.created_at
                ? new Date(comment.created_at).toLocaleString("zh-CN")
                : ""}
            </p>
            <p className="mt-2 text-sm">{comment.content}</p>
          </div>
          {canDelete && (
            <Button
              variant="ghost"
              size="sm"
              className="text-destructive text-xs"
              disabled={deleteComment.isPending}
              onClick={() => {
                deleteComment.mutateAsync(comment.id).then(onDelete);
              }}
            >
              删除
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function CommentForm({
  postSlug,
  onSuccess,
}: {
  postSlug: string;
  onSuccess: () => void;
}) {
  const isAuthenticated = useIsAuthenticated();
  const currentUser = useCurrentUser();
  const createComment = useCreateComment();

  const defaultAuthorName = currentUser?.username ?? "";
  const [authorName, setAuthorName] = useState(defaultAuthorName);
  const [content, setContent] = useState("");

  if (!isAuthenticated) {
    return (
      <p className="text-sm text-muted-foreground">
        <a href="/login" className="underline">
          登录
        </a>{" "}
        后才能发表评论。
      </p>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    try {
      await createComment.mutateAsync({
        slug: postSlug,
        data: { author_name: authorName || currentUser?.username || "匿名", content },
      });
      setContent("");
      onSuccess();
    } catch {
      // error handled by mutation
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="space-y-2">
        <Label htmlFor="author">昵称</Label>
        <Input
          id="author"
          value={authorName}
          onChange={(e) => setAuthorName(e.target.value)}
          placeholder={currentUser?.username ?? "你的昵称"}
          required
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="content">评论</Label>
        <Textarea
          id="content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="写下你的评论..."
          rows={3}
          required
        />
      </div>
      <Button type="submit" disabled={createComment.isPending}>
        {createComment.isPending ? "提交中..." : "提交评论"}
      </Button>
    </form>
  );
}