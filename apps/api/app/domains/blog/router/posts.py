"""
博客文章 API 路由模块

提供文章 CRUD + 归档 + 后台管理的 RESTful API 端点。
"""

import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
    require_scope,
)
from app.core.schemas import Message, PaginationParams
from app.core.scopes import BlogScope
from app.core.errors import (
    raise_blog_post_not_found,
    raise_blog_post_slug_taken,
    raise_blog_forbidden_not_author,
    raise_permission_denied,
)

from app.domains.blog import repository
from app.domains.blog.schemas import (
    ArchiveEntry,
    ArchivePostBrief,
    ArchiveResponse,
    CategoryPublic,
    PostCreate,
    PostDetailPublic,
    PostPublic,
    PostsPublic,
    PostUpdate,
)

router = APIRouter()


# ======================== 公开端点 ========================

@router.get("/", response_model=PostsPublic)
async def list_posts(
    session: SessionDep,
    pagination: Annotated[PaginationParams, Query()],
    q: str | None = Query(None, alias="q", description="搜索关键词"),
    category: str | None = Query(None, alias="category", description="分类 slug"),
) -> Any:
    """
    公开文章列表（仅已发布）。

    权限：公开
    支持搜索（q）和分类筛选（category）
    """
    posts, count = await repository.get_posts(
        session=session,
        skip=pagination.offset,
        limit=pagination.limit,
        search=q,
        category_slug=category,
        published_only=True,
    )

    items: list[PostPublic] = []
    for p in posts:
        items.append(PostPublic(
            id=p.id,
            slug=p.slug,
            title=p.title,
            excerpt=p.excerpt,
            is_published=p.is_published,
            category_id=p.category_id,
            category=CategoryPublic(
                id=p.category.id, name=p.category.name, slug=p.category.slug,
                post_count=0, created_at=p.category.created_at,
            ) if p.category else None,
            author_id=p.author_id,
            author_name=p.author.username if p.author else None,
            comments_count=len(p.comments) if p.comments else 0,
            published_at=p.published_at,
            created_at=p.created_at,
            updated_at=p.updated_at,
        ))

    return PostsPublic(
        data=items,
        count=count,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(count + pagination.page_size - 1) // pagination.page_size if count > 0 else 0,
    )


@router.get("/archives", response_model=ArchiveResponse)
async def get_archives(session: SessionDep) -> Any:
    """
    归档视图：按年/月聚合所有已发布文章。

    权限：公开
    """
    raw = await repository.list_archives(session=session)

    entries: list[ArchiveEntry] = []
    for group in raw:
        briefs: list[ArchivePostBrief] = []
        for p in group["posts"]:
            briefs.append(ArchivePostBrief(
                slug=p["slug"],
                title=p["title"],
                published_at=p["published_at"],
            ))
        entries.append(ArchiveEntry(
            year=group["year"],
            month=group["month"],
            posts=briefs,
        ))

    return ArchiveResponse(archives=entries)


@router.get("/{slug}", response_model=PostDetailPublic)
async def get_post_detail(slug: str, session: SessionDep) -> Any:
    """
    文章详情（含正文 body）。

    权限：公开（仅已发布），后台可查看未发布
    """
    post = await repository.get_post_by_slug(session=session, slug=slug)
    if not post:
        raise_blog_post_not_found()

    # 公开视图仅允许查看已发布的文章
    # (如果需要未发布也可见，走 admin 详情接口)
    if not post.is_published:
        raise_blog_post_not_found()

    return PostDetailPublic(
        id=post.id,
        slug=post.slug,
        title=post.title,
        excerpt=post.excerpt,
        body=post.body,
        is_published=post.is_published,
        category_id=post.category_id,
        category=CategoryPublic(
            id=post.category.id, name=post.category.name, slug=post.category.slug,
            post_count=0, created_at=post.category.created_at,
        ) if post.category else None,
        author_id=post.author_id,
        author_name=post.author.username if post.author else None,
        comments_count=len(post.comments) if post.comments else 0,
        published_at=post.published_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


# ======================== 后台端点（需 scope） ========================

@router.get(
    "/admin/list",
    response_model=PostsPublic,
    dependencies=[Depends(require_scope(BlogScope.UPDATE))],
)
async def admin_list_posts(
    session: SessionDep,
    current_user: CurrentUser,
    pagination: Annotated[PaginationParams, Query()],
    q: str | None = Query(None, alias="q"),
) -> Any:
    """
    后台文章列表（含未发布）。

    权限：BlogScope.UPDATE
    """
    posts, count = await repository.get_posts(
        session=session,
        skip=pagination.offset,
        limit=pagination.limit,
        search=q,
        published_only=False,
    )

    items: list[PostPublic] = []
    for p in posts:
        items.append(PostPublic(
            id=p.id,
            slug=p.slug,
            title=p.title,
            excerpt=p.excerpt,
            is_published=p.is_published,
            category_id=p.category_id,
            category=CategoryPublic(
                id=p.category.id, name=p.category.name, slug=p.category.slug,
                post_count=0, created_at=p.category.created_at,
            ) if p.category else None,
            author_id=p.author_id,
            author_name=p.author.username if p.author else None,
            comments_count=len(p.comments) if p.comments else 0,
            published_at=p.published_at,
            created_at=p.created_at,
            updated_at=p.updated_at,
        ))

    return PostsPublic(
        data=items,
        count=count,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(count + pagination.page_size - 1) // pagination.page_size if count > 0 else 0,
    )


@router.post(
    "/",
    response_model=PostPublic,
    dependencies=[Depends(require_scope(BlogScope.CREATE))],
)
async def create_post(
    *, session: SessionDep, current_user: CurrentUser, post_in: PostCreate
) -> Any:
    """
    创建新文章。

    权限：BlogScope.CREATE
    """
    # 检查 slug 唯一性
    existing = await repository.get_post_by_slug(session=session, slug=post_in.slug)
    if existing:
        raise_blog_post_slug_taken(f"Post slug '{post_in.slug}' already exists")

    post = await repository.create_post(
        session=session, post_in=post_in, author_id=current_user.id
    )

    # 重新加载关联
    post = await repository.get_post_by_slug(session=session, slug=post.slug)

    return PostPublic(
        id=post.id,
        slug=post.slug,
        title=post.title,
        excerpt=post.excerpt,
        is_published=post.is_published,
        category_id=post.category_id,
        category=CategoryPublic(
            id=post.category.id, name=post.category.name, slug=post.category.slug,
            post_count=0, created_at=post.category.created_at,
        ) if post.category else None,
        author_id=post.author_id,
        author_name=post.author.username if post.author else None,
        comments_count=0,
        published_at=post.published_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.patch(
    "/{post_id}",
    response_model=PostPublic,
)
async def update_post(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    post_id: uuid.UUID,
    post_in: PostUpdate,
) -> Any:
    """
    更新文章。

    权限：作者本人或 BlogScope.ADMIN
    """
    post = await repository.get_post(session=session, post_id=post_id)
    if not post:
        raise_blog_post_not_found()

    # 权限检查：作者本人或 admin scope
    if post.author_id != current_user.id:
        from app.core.dependencies import get_user_scopes
        user_scopes = await get_user_scopes(session, current_user)
        if BlogScope.ADMIN.value not in user_scopes:
            raise_blog_forbidden_not_author("Only the author or admin can update this post")

    # 若更新 slug，检查唯一性
    if post_in.slug and post_in.slug != post.slug:
        existing = await repository.get_post_by_slug(session=session, slug=post_in.slug)
        if existing:
            raise_blog_post_slug_taken(f"Post slug '{post_in.slug}' already exists")

    post = await repository.update_post(session=session, db_post=post, post_in=post_in)

    # 重新加载
    post = await repository.get_post_by_slug(session=session, slug=post.slug)

    return PostPublic(
        id=post.id,
        slug=post.slug,
        title=post.title,
        excerpt=post.excerpt,
        is_published=post.is_published,
        category_id=post.category_id,
        category=CategoryPublic(
            id=post.category.id, name=post.category.name, slug=post.category.slug,
            post_count=0, created_at=post.category.created_at,
        ) if post.category else None,
        author_id=post.author_id,
        author_name=post.author.username if post.author else None,
        comments_count=len(post.comments) if post.comments else 0,
        published_at=post.published_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.delete("/{post_id}")
async def delete_post(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    post_id: uuid.UUID,
) -> Message:
    """
    删除文章。

    权限：作者本人或 BlogScope.ADMIN
    """
    post = await repository.get_post(session=session, post_id=post_id)
    if not post:
        raise_blog_post_not_found()

    # 权限检查
    if post.author_id != current_user.id:
        from app.core.dependencies import get_user_scopes
        user_scopes = await get_user_scopes(session, current_user)
        if BlogScope.ADMIN.value not in user_scopes:
            raise_blog_forbidden_not_author("Only the author or admin can delete this post")

    await repository.delete_post(session=session, db_post=post)
    return Message(message="Post deleted successfully")