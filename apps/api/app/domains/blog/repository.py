"""
Blog 域 Repository 层

提供博客分类、文章、评论的全部 CRUD 操作，
遵循与 user 域一致的模块级 async def 函数约定。
"""

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select as sm_select

from app.core.models import BlogCategory, BlogComment, BlogPost
from app.domains.blog.schemas import (
    CategoryCreate,
    CategoryUpdate,
    CommentCreate,
    PostCreate,
    PostUpdate,
)

# ============================== Category CRUD ==============================

async def get_category(*, session: AsyncSession, category_id: uuid.UUID) -> BlogCategory | None:
    """通过 ID 查询分类"""
    return await session.get(BlogCategory, category_id)


async def get_category_by_slug(*, session: AsyncSession, slug: str) -> BlogCategory | None:
    """通过 slug 查询分类"""
    statement = select(BlogCategory).where(BlogCategory.slug == slug)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_categories(
    *, session: AsyncSession, skip: int = 0, limit: int = 100
) -> Tuple[list[BlogCategory], int]:
    """分页获取分类列表（含文章计数通过单独查询获取）"""
    count_st = select(func.count()).select_from(BlogCategory)
    result = await session.execute(count_st)
    count = result.scalar_one()

    statement = (
        select(BlogCategory)
        .order_by(BlogCategory.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(statement)
    categories = result.scalars().all()
    return list(categories), count


async def create_category(
    *, session: AsyncSession, category_in: CategoryCreate
) -> BlogCategory:
    """创建新分类"""
    db_obj = BlogCategory.model_validate(category_in)
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def update_category(
    *, session: AsyncSession, db_category: BlogCategory, category_in: CategoryUpdate
) -> BlogCategory:
    """更新已有分类"""
    update_data = category_in.model_dump(exclude_unset=True)
    db_category.sqlmodel_update(update_data)
    session.add(db_category)
    await session.commit()
    await session.refresh(db_category)
    return db_category


async def delete_category(*, session: AsyncSession, db_category: BlogCategory) -> None:
    """删除分类"""
    await session.delete(db_category)
    await session.commit()


async def count_posts_by_category(*, session: AsyncSession) -> dict[uuid.UUID, int]:
    """一次性查询所有分类的文章计数"""
    statement = (
        select(BlogPost.category_id, func.count(BlogPost.id))
        .where(BlogPost.is_published == True)  # noqa: E712
        .group_by(BlogPost.category_id)
    )
    result = await session.execute(statement)
    rows = result.all()
    return {row[0]: row[1] for row in rows if row[0] is not None}


# ============================== Post CRUD ==============================

async def get_post(*, session: AsyncSession, post_id: uuid.UUID) -> BlogPost | None:
    """通过 ID 查询文章"""
    return await session.get(BlogPost, post_id)


async def get_post_by_slug(*, session: AsyncSession, slug: str) -> BlogPost | None:
    """通过 slug 查询文章（预加载 category 避免 N+1）"""
    statement = (
        select(BlogPost)
        .where(BlogPost.slug == slug)
        .options(selectinload(BlogPost.category))
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_posts(
    *,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    category_slug: str | None = None,
    search: str | None = None,
    published_only: bool = True,
) -> Tuple[list[BlogPost], int]:
    """
    分页获取文章列表

    Args:
        published_only: True 仅返回已发布（公开视图），False 返回全部（后台视图）
        category_slug: 按分类筛选
        search: 标题/摘要模糊搜索
    """
    # 构建基查询
    base = select(BlogPost).options(selectinload(BlogPost.category))

    if published_only:
        base = base.where(BlogPost.is_published == True)  # noqa: E712

    if category_slug:
        base = base.join(BlogCategory, BlogPost.category_id == BlogCategory.id).where(
            BlogCategory.slug == category_slug
        )

    if search:
        pattern = f"%{search}%"
        base = base.where(
            (BlogPost.title.ilike(pattern)) | (BlogPost.excerpt.ilike(pattern))
        )

    # 计数
    count_st = (
        select(func.count())
        .select_from(BlogPost)
    )
    if published_only:
        count_st = count_st.where(BlogPost.is_published == True)  # noqa: E712
    if category_slug:
        count_st = count_st.join(BlogCategory, BlogPost.category_id == BlogCategory.id).where(
            BlogCategory.slug == category_slug
        )
    if search:
        count_st = count_st.where(
            (BlogPost.title.ilike(pattern)) | (BlogPost.excerpt.ilike(pattern))
        )
    result = await session.execute(count_st)
    count = result.scalar_one()

    # 排序：按 published_at 倒序（未发布按 created_at）
    order_col = func.coalesce(BlogPost.published_at, BlogPost.created_at)
    statement = base.order_by(order_col.desc()).offset(skip).limit(limit)

    result = await session.execute(statement)
    posts = result.scalars().all()
    return list(posts), count


async def create_post(
    *, session: AsyncSession, post_in: PostCreate, author_id: uuid.UUID
) -> BlogPost:
    """创建新文章"""
    db_obj = BlogPost.model_validate(
        post_in,
        update={
            "author_id": author_id,
            "updated_at": datetime.now(timezone.utc),
        },
    )
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def update_post(
    *, session: AsyncSession, db_post: BlogPost, post_in: PostUpdate
) -> BlogPost:
    """更新已有文章"""
    update_data = post_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)
    db_post.sqlmodel_update(update_data)
    session.add(db_post)
    await session.commit()
    await session.refresh(db_post)
    return db_post


async def delete_post(*, session: AsyncSession, db_post: BlogPost) -> None:
    """删除文章"""
    await session.delete(db_post)
    await session.commit()


# ============================== Archive ==============================

async def list_archives(*, session: AsyncSession) -> list[dict]:
    """
    获取归档数据：按年/月聚合所有已发布文章

    Returns:
        [{year: 2025, month: 12, posts: [{slug, title, published_at}]}, ...]
    """
    statement = (
        select(BlogPost.slug, BlogPost.title, BlogPost.published_at)
        .where(BlogPost.is_published == True)  # noqa: E712
        .order_by(BlogPost.published_at.desc())
    )
    result = await session.execute(statement)
    rows = result.all()

    # Python 端按年/月聚合
    groups = defaultdict(list)
    for slug, title, published_at in rows:
        if published_at:
            key = (published_at.year, published_at.month)
            groups[key].append({
                "slug": slug,
                "title": title,
                "published_at": published_at,
            })

    archives = []
    for (year, month), posts in sorted(groups.items(), reverse=True):
        archives.append({"year": year, "month": month, "posts": posts})

    return archives


# ============================== Comment CRUD ==============================

async def get_comment(*, session: AsyncSession, comment_id: uuid.UUID) -> BlogComment | None:
    """通过 ID 查询评论"""
    return await session.get(BlogComment, comment_id)


async def get_comments(
    *,
    session: AsyncSession,
    post_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[list[BlogComment], int]:
    """分页获取指定文章的评论"""
    count_st = (
        select(func.count())
        .select_from(BlogComment)
        .where(BlogComment.post_id == post_id)
    )
    result = await session.execute(count_st)
    count = result.scalar_one()

    statement = (
        select(BlogComment)
        .where(BlogComment.post_id == post_id)
        .order_by(BlogComment.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(statement)
    comments = result.scalars().all()
    return list(comments), count


async def create_comment(
    *,
    session: AsyncSession,
    comment_in: CommentCreate,
    post_id: uuid.UUID,
    author_id: uuid.UUID | None = None,
) -> BlogComment:
    """创建新评论"""
    update = {"post_id": post_id}
    if author_id:
        update["author_id"] = author_id
    db_obj = BlogComment.model_validate(comment_in, update=update)
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def delete_comment(*, session: AsyncSession, db_comment: BlogComment) -> None:
    """删除评论"""
    await session.delete(db_comment)
    await session.commit()


async def list_recent_comments(
    *, session: AsyncSession, limit: int = 8
) -> list[BlogComment]:
    """获取最近 N 条评论（预加载关联文章）"""
    statement = (
        select(BlogComment)
        .options(selectinload(BlogComment.post))
        .order_by(BlogComment.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())