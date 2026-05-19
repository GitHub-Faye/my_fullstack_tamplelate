"""
Blog 域 DTO / Schema 定义模块

提供博客分类、文章、评论的完整请求/响应 DTO，
遵循与 user 域一致的 Base / Create / Update / Public 分层约定。
"""

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.core.schemas import PaginatedResponse


# ======================== Category DTOs ========================

class CategoryBase(SQLModel):
    """分类共享属性"""
    name: str = Field(max_length=50)
    slug: str = Field(max_length=50)


class CategoryCreate(CategoryBase):
    """创建分类请求"""
    pass


class CategoryUpdate(SQLModel):
    """更新分类请求（所有字段可选）"""
    name: str | None = Field(default=None, max_length=50)
    slug: str | None = Field(default=None, max_length=50)


class CategoryPublic(CategoryBase):
    """公开分类响应（含文章计数）"""
    id: uuid.UUID
    post_count: int = 0
    created_at: datetime | None = None


class CategoriesPublic(PaginatedResponse[CategoryPublic]):
    """分类分页响应"""
    pass


# ======================== Post DTOs ========================

class PostBase(SQLModel):
    """文章共享属性"""
    slug: str = Field(max_length=255)
    title: str = Field(max_length=255)
    excerpt: str | None = Field(default=None, max_length=500)
    body: str = Field()
    is_published: bool = False


class PostCreate(PostBase):
    """创建文章请求"""
    category_id: uuid.UUID | None = None
    published_at: datetime | None = None


class PostUpdate(SQLModel):
    """更新文章请求（所有字段可选）"""
    slug: str | None = Field(default=None, max_length=255)
    title: str | None = Field(default=None, max_length=255)
    excerpt: str | None = Field(default=None, max_length=500)
    body: str | None = None
    category_id: uuid.UUID | None = None
    is_published: bool | None = None
    published_at: datetime | None = None


class PostPublic(SQLModel):
    """公开文章响应（列表视图，不含 body）"""
    id: uuid.UUID
    slug: str
    title: str
    excerpt: str | None = None
    is_published: bool
    category_id: uuid.UUID | None = None
    category: CategoryPublic | None = None
    author_id: uuid.UUID
    author_name: str | None = None
    comments_count: int = 0
    published_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PostDetailPublic(PostPublic):
    """文章详情响应（包含 body）"""
    body: str


class PostsPublic(PaginatedResponse[PostPublic]):
    """文章分页响应"""
    pass


# ======================== Archive DTOs ========================

class ArchivePostBrief(SQLModel):
    """归档文章简要信息"""
    slug: str
    title: str
    published_at: datetime | None = None


class ArchiveEntry(SQLModel):
    """单条归档记录（某年某月）"""
    year: int
    month: int
    posts: list[ArchivePostBrief]


class ArchiveResponse(SQLModel):
    """归档响应"""
    archives: list[ArchiveEntry]


# ======================== Comment DTOs ========================

class CommentBase(SQLModel):
    """评论共享属性"""
    author_name: str = Field(max_length=80)
    content: str


class CommentCreate(CommentBase):
    """创建评论请求"""
    pass


class CommentUpdate(SQLModel):
    """更新评论请求"""
    author_name: str | None = Field(default=None, max_length=80)
    content: str | None = None


class CommentPublic(SQLModel):
    """公开评论响应"""
    id: uuid.UUID
    post_id: uuid.UUID
    author_id: uuid.UUID | None = None
    author_name: str
    content: str
    created_at: datetime | None = None


class CommentsPublic(PaginatedResponse[CommentPublic]):
    """评论分页响应"""
    pass


class RecentCommentPublic(SQLModel):
    """最近评论响应（用于侧栏）"""
    id: uuid.UUID
    author_name: str
    post_slug: str
    post_title: str
    content: str  # 展示摘要
    created_at: datetime | None = None