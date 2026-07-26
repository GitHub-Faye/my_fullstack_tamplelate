"use client";

import { useCallback, useRef, useState } from "react";
import { Paperclip, X, Loader2, FileText, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  uploadAttachmentV1TasksTaskIdAttachmentsPost,
  listAttachmentsV1TasksTaskIdAttachmentsGet,
  deleteAttachmentV1TasksAttachmentsAttachmentIdDelete,
} from "@repo/sdk";
import { toast } from "sonner";
import { formatDateTime } from "@/lib/utils";

interface Attachment {
  id: string;
  file_name: string;
  file_size: number;
  uploaded_by: string;
  created_at?: string | null;
}

/**
 * 附件上传组件
 *
 * 创建任务成功后，显示附件上传区域。
 * 支持多文件上传、已上传文件列表展示、下载和删除。
 */
export function AttachmentUpload({
  taskId,
  onUploadingChange,
}: {
  taskId: string;
  onUploadingChange?: (uploading: boolean) => void;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  // 加载附件列表
  const loadAttachments = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listAttachmentsV1TasksTaskIdAttachmentsGet({
        path: { task_id: taskId },
        throwOnError: true,
      });
      setAttachments(res.data as unknown as Attachment[]);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  // 初次加载
  const loadedRef = useRef(false);
  if (!loadedRef.current) {
    loadedRef.current = true;
    loadAttachments();
  }

  // 选择文件并上传
  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files?.length) return;

      setUploading(true);
      onUploadingChange?.(true);

      try {
        for (let i = 0; i < files.length; i++) {
          const file = files[i] as File;
          const formData = new FormData();
          formData.append("file", file);

          await uploadAttachmentV1TasksTaskIdAttachmentsPost({
            path: { task_id: taskId },
            body: { file },
            throwOnError: true,
          });
        }
        toast.success(`已上传 ${files.length} 个文件`);
        await loadAttachments();
      } catch (err: any) {
        toast.error(err.message || "上传失败");
      } finally {
        setUploading(false);
        onUploadingChange?.(false);
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      }
    },
    [taskId, loadAttachments, onUploadingChange]
  );

  // 删除附件
  const handleDelete = useCallback(
    async (attachmentId: string, fileName: string) => {
      try {
        await deleteAttachmentV1TasksAttachmentsAttachmentIdDelete({
          path: { attachment_id: attachmentId },
          throwOnError: true,
        });
        toast.success(`已删除 ${fileName}`);
        await loadAttachments();
      } catch (err: any) {
        toast.error(err.message || "删除失败");
      }
    },
    [loadAttachments]
  );

  // 下载附件
  const handleDownload = useCallback(
    (attachmentId: string, fileName: string) => {
      const baseUrl =
        (typeof window !== "undefined"
          ? window.location.origin
          : "http://localhost:8000") + "/v1";
      const url = `${baseUrl}/tasks/attachments/${attachmentId}/download`;
      const a = document.createElement("a");
      a.href = url;
      a.download = fileName;
      a.click();
    },
    []
  );

  // 格式化文件大小
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium leading-none">附件</label>

      {/* 上传按钮 */}
      <div className="flex items-center gap-2">
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleFileChange}
          disabled={uploading}
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={uploading}
          onClick={() => fileInputRef.current?.click()}
        >
          {uploading ? (
            <>
              <Loader2 className="mr-1 h-4 w-4 animate-spin" />
              上传中...
            </>
          ) : (
            <>
              <Paperclip className="mr-1 h-4 w-4" />
              选择文件
            </>
          )}
        </Button>
      </div>

      {/* 文件列表 */}
      {loading && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-3 w-3 animate-spin" />
          加载中...
        </div>
      )}

      {!loading && attachments.length > 0 && (
        <div className="space-y-1">
          {attachments.map((att) => (
            <div
              key={att.id}
              className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
            >
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                <span className="truncate">{att.file_name}</span>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {formatSize(att.file_size)}
                </span>
              </div>
              <div className="flex items-center gap-1 shrink-0 ml-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => handleDownload(att.id, att.file_name)}
                  title="下载"
                >
                  <Download className="h-3.5 w-3.5" />
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-destructive hover:text-destructive"
                  onClick={() => handleDelete(att.id, att.file_name)}
                  title="删除"
                >
                  <X className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && attachments.length === 0 && (
        <p className="text-xs text-muted-foreground">
          暂无附件，点击上方按钮选择文件上传
        </p>
      )}
    </div>
  );
}