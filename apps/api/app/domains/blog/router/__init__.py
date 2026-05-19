from app.domains.blog.router.categories import router as categories_router
from app.domains.blog.router.posts import router as posts_router
from app.domains.blog.router.comments import router as comments_router

__all__ = ["posts_router", "categories_router", "comments_router"]