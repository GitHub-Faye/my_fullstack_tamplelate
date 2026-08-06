"""
Task 模块附件管理路由

提供附件的上传、列表、下载、删除功能。
文件通过 aiofiles 写入本地存储，元数据存入数据库。
"""

import uuid
from typing import Annotated, Any
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import FileResponse

from app.core.dependencies import CurrentUser, SessionDep, require_any_scope
from app.core.scopes import TaskScope
from app.core.models import Attachment, Task
from app.core.config import get_settings
from app.core.errors import BusinessException, ErrorCode
from app.domains.task.dependencies import get_task_or_404

router = APIRouter()

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg",
    ".zip", ".rar", ".7z",
    ".txt", ".md", ".csv", ".html",
}

# 图片扩展名 → 真实 MIME 类型映射（用于内联预览）
IMAGE_MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".svg": "image/svg+xml",
}


@router.post(
    "/{task_id}/attachments",
    summary="上传附件",
    description="PM 或管理员为指定任务上传附件，返回附件元数据",
)
async def upload_attachment(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task: Annotated[Task, Depends(get_task_or_404)],
    file: UploadFile = File(..., description="附件文件"),
    _: Annotated[None, Depends(require_any_scope(TaskScope.UPDATE, TaskScope.ADMIN))],
) -> Any:
    """上传附件到指定任务"""
    settings = get_settings()

    # 检查文件大小
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise BusinessException(
            code=ErrorCode.ATTACHMENT_TOO_LARGE,
            detail=f"File too large. Max size is {settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB",
        )

    # 检查文件扩展名
    ext = Path(file.filename or "").suffix.lower()
    if ext and ext not in ALLOWED_EXTENSIONS:
        raise BusinessException(
            code=ErrorCode.ATTACHMENT_INVALID_TYPE,
            detail=f"File type '{ext}' is not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # 确保存储目录存在
    task_dir = Path(settings.UPLOAD_DIR) / str(task.id)
    task_dir.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名
    file_id = uuid.uuid4()
    stored_name = f"{file_id}{ext}"
    file_path = task_dir / stored_name

    # 写入文件
    import aiofiles
    async with aiofiles.open(str(file_path), "wb") as f:
        await f.write(contents)

    # 数据库记录
    attachment = Attachment(
        file_name=file.filename or stored_name,
        file_path=str(file_path),
        file_size=len(contents),
        task_id=task.id,
        uploaded_by=current_user.id,
    )
    session.add(attachment)
    await session.commit()
    await session.refresh(attachment)

    return attachment


@router.get(
    "/{task_id}/attachments",
    summary="获取附件列表",
    description="获取指定任务的所有附件元数据",
)
async def list_attachments(
    *,
    session: SessionDep,
    task: Annotated[Task, Depends(get_task_or_404)],
    _: Annotated[None, Depends(require_any_scope(TaskScope.READ, TaskScope.ADMIN))],
) -> Any:
    """获取任务附件列表"""
    from sqlmodel import select
    stmt = select(Attachment).where(Attachment.task_id == task.id).order_by(Attachment.created_at.desc())
    result = await session.execute(stmt)
    attachments = result.scalars().all()
    return attachments


@router.get(
    "/attachments/{attachment_id}/download",
    summary="下载/预览附件",
    description="下载指定附件文件",
)
async def download_attachment(
    *,
    session: SessionDep,
    attachment_id: uuid.UUID,
    _current_user: CurrentUser,
) -> Any:
    """下载附件"""
    attachment = await session.get(Attachment, attachment_id)
    if not attachment:
        raise BusinessException(
            code=ErrorCode.ATTACHMENT_NOT_FOUND,
            detail="Attachment not found",
        )

    file_path = Path(attachment.file_path)
    if not file_path.exists():
        raise BusinessException(
            code=ErrorCode.ATTACHMENT_NOT_FOUND,
            detail="File not found on disk",
        )

    # 图片类型使用真实 MIME 并内联展示（浏览器可直接打开预览）
    # 其余类型强制下载
    ext = file_path.suffix.lower()
    media_type = IMAGE_MEDIA_TYPES.get(ext, "application/octet-stream")
    disposition = "inline" if ext in IMAGE_MEDIA_TYPES else "attachment"

    return FileResponse(
        path=str(file_path),
        filename=attachment.file_name,
        media_type=media_type,
        content_disposition_type=disposition,
    )


@router.delete(
    "/attachments/{attachment_id}",
    summary="删除附件",
    description="删除指定附件（文件 + 数据库记录）",
)
async def delete_attachment(
    *,
    session: SessionDep,
    attachment_id: uuid.UUID,
    current_user: CurrentUser,
    _: Annotated[None, Depends(require_any_scope(TaskScope.UPDATE, TaskScope.ADMIN))],
) -> Any:
    """删除附件"""
    attachment = await session.get(Attachment, attachment_id)
    if not attachment:
        raise BusinessException(
            code=ErrorCode.ATTACHMENT_NOT_FOUND,
            detail="Attachment not found",
        )

    # 删除文件
    file_path = Path(attachment.file_path)
    if file_path.exists():
        file_path.unlink()

    # 删除数据库记录
    await session.delete(attachment)
    await session.commit()

    return {"message": "Attachment deleted successfully"}