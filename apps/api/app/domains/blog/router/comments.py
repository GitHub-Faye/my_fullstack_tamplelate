"""
博客评论 API 路由模块

提供评论 CRUD + 最近评论的 RESTful API 端点。
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.schemas import Message, PaginationParams
from app.core.scopes import BlogScope
from app.core.errors import (
    raise_blog_post_not_found,
    raise_blog_comment_not_found,
    raise_blog_forbidden_not_author,
)

from app.domains.blog import repository
from app.domains.blog.schemas import (
    CommentCreate,
    CommentPublic,
    CommentsPublic,
    RecentCommentPublic,
)

router = APIRouter()


# ======================== 公开端点 ========================

@router.get("/posts/{slug}/comments", response_model=CommentsPublic)
async def list_comments(
    slug: str,
    session: SessionDep,
    pagination: Annotated[PaginationParams, Query()],
) -> Any:
    """
    获取指定文章的评论列表（分页）。

    权限：公开
    """
    post = await repository.get_post_by_slug(session=session, slug=slug)
    if not post:
        raise_blog_post_not_found()

    comments, count = await repository.get_comments(
        session=session,
        post_id=post.id,
        skip=pagination.offset,
        limit=pagination.limit,
    )

    items: list[CommentPublic] = []
    for c in comments:
        items.append(CommentPublic(
            id=c.id,
            post_id=c.post_id,
            author_id=c.author_id,
            author_name=c.author_name,
            content=c.content,
            created_at=c.created_at,
        ))

    return CommentsPublic(
        data=items,
        count=count,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(count + pagination.page_size - 1) // pagination.page_size if count > 0 else 0,
    )


@router.post("/posts/{slug}/comments", response_model=CommentPublic)
async def create_comment(
    *,
    slug: str,
    session: SessionDep,
    comment_in: CommentCreate,
    current_user: CurrentUser,
) -> Any:
    """
    提交新评论。

    权限：登录用户（不允许匿名）
    """
    post = await repository.get_post_by_slug(session=session, slug=slug)
    if not post:
        raise_blog_post_not_found()

    comment = await repository.create_comment(
        session=session,
        comment_in=comment_in,
        post_id=post.id,
        author_id=current_user.id,
    )

    return CommentPublic(
        id=comment.id,
        post_id=comment.post_id,
        author_id=comment.author_id,
        author_name=comment.author_name,
        content=comment.content,
        created_at=comment.created_at,
    )


@router.get("/comments/recent", response_model=list[RecentCommentPublic])
async def get_recent_comments(
    session: SessionDep,
    limit: int = Query(8, ge=1, le=50),
) -> Any:
    """
    最近评论（用于侧栏展示）。

    权限：公开
    """
    comments = await repository.list_recent_comments(session=session, limit=limit)

    items: list[RecentCommentPublic] = []
    for c in comments:
        items.append(RecentCommentPublic(
            id=c.id,
            author_name=c.author_name,
            post_slug=c.post.slug if c.post else "",
            post_title=c.post.title if c.post else "",
            content=c.content[:200],  # 摘要截断
            created_at=c.created_at,
        ))

    return items


# ======================== 后台端点 ========================

@router.delete("/comments/{comment_id}")
async def delete_comment(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    comment_id: uuid.UUID,
) -> Message:
    """
    删除评论。

    权限：评论作者或 BlogScope.ADMIN
    """
    comment = await repository.get_comment(session=session, comment_id=comment_id)
    if not comment:
        raise_blog_comment_not_found()

    # 权限检查：评论作者或 admin
    if comment.author_id != current_user.id:
        from app.core.dependencies import get_user_scopes
        user_scopes = await get_user_scopes(session, current_user)
        if BlogScope.ADMIN.value not in user_scopes:
            raise_blog_forbidden_not_author("Only comment author or admin can delete comments")

    await repository.delete_comment(session=session, db_comment=comment)
    return Message(message="Comment deleted successfully")