"""
博客分类 API 路由模块

提供分类 CRUD + 按分类筛选文章的 RESTful API 端点。
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.schemas import PaginationParams
from app.core.scopes import BlogScope

from app.domains.blog import repository
from app.domains.blog.schemas import (
    CategoriesPublic,
    CategoryCreate,
    CategoryPublic,
    CategoryUpdate,
    PostsPublic,
    PostPublic,
)
from app.core.errors import (
    raise_blog_category_not_found,
    raise_blog_category_slug_taken,
)

# -------- 由于 require_scope 签名已泛型化，直接使用 core 中的 -------
from app.core.dependencies import require_scope

router = APIRouter()


# ======================== 公开端点 ========================

@router.get("/", response_model=CategoriesPublic)
async def list_categories(
    session: SessionDep,
    pagination: Annotated[PaginationParams, Query()],
) -> Any:
    """
    获取全量分类列表（含各分类文章计数）。

    权限：公开
    """
    categories, count = await repository.get_categories(
        session=session,
        skip=pagination.offset,
        limit=pagination.limit,
    )

    # 批量查询文章计数
    post_counts = await repository.count_posts_by_category(session=session)

    items: list[CategoryPublic] = []
    for cat in categories:
        items.append(CategoryPublic(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            post_count=post_counts.get(cat.id, 0),
            created_at=cat.created_at,
        ))

    return CategoriesPublic(
        data=items,
        count=count,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(count + pagination.page_size - 1) // pagination.page_size if count > 0 else 0,
    )


@router.get("/{slug}/posts", response_model=PostsPublic)
async def list_category_posts(
    slug: str,
    session: SessionDep,
    pagination: Annotated[PaginationParams, Query()],
) -> Any:
    """
    获取指定分类下的已发布文章列表（分页）。

    权限：公开
    """
    category = await repository.get_category_by_slug(session=session, slug=slug)
    if not category:
        raise_blog_category_not_found(f"Category '{slug}' not found")

    posts, count = await repository.get_posts(
        session=session,
        skip=pagination.offset,
        limit=pagination.limit,
        category_slug=slug,
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


# ======================== 后台端点（需 BlogScope.ADMIN） ========================

@router.post(
    "/",
    response_model=CategoryPublic,
    dependencies=[Depends(require_scope(BlogScope.ADMIN))],
)
async def create_category(
    *, session: SessionDep, category_in: CategoryCreate, current_user: CurrentUser
) -> Any:
    """
    创建新分类。

    权限：BlogScope.ADMIN
    """
    existing = await repository.get_category_by_slug(session=session, slug=category_in.slug)
    if existing:
        raise_blog_category_slug_taken(f"Category slug '{category_in.slug}' already exists")

    category = await repository.create_category(session=session, category_in=category_in)

    return CategoryPublic(
        id=category.id,
        name=category.name,
        slug=category.slug,
        post_count=0,
        created_at=category.created_at,
    )


@router.patch(
    "/{category_id}",
    response_model=CategoryPublic,
    dependencies=[Depends(require_scope(BlogScope.ADMIN))],
)
async def update_category(
    *, session: SessionDep, category_id: uuid.UUID, category_in: CategoryUpdate
) -> Any:
    """
    更新分类。

    权限：BlogScope.ADMIN
    """
    category = await repository.get_category(session=session, category_id=category_id)
    if not category:
        raise_blog_category_not_found()

    # 若更新 slug，检查唯一性
    if category_in.slug and category_in.slug != category.slug:
        existing = await repository.get_category_by_slug(session=session, slug=category_in.slug)
        if existing:
            raise_blog_category_slug_taken(f"Category slug '{category_in.slug}' already exists")

    category = await repository.update_category(
        session=session, db_category=category, category_in=category_in
    )

    post_counts = await repository.count_posts_by_category(session=session)
    return CategoryPublic(
        id=category.id,
        name=category.name,
        slug=category.slug,
        post_count=post_counts.get(category.id, 0),
        created_at=category.created_at,
    )


@router.delete(
    "/{category_id}",
    dependencies=[Depends(require_scope(BlogScope.ADMIN))],
)
async def delete_category(
    *, session: SessionDep, category_id: uuid.UUID, current_user: CurrentUser
) -> dict:
    """
    删除分类。

    权限：BlogScope.ADMIN
    """
    category = await repository.get_category(session=session, category_id=category_id)
    if not category:
        raise_blog_category_not_found()

    await repository.delete_category(session=session, db_category=category)
    return {"message": "Category deleted successfully"}