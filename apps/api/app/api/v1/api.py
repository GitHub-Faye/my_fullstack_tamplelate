from fastapi import APIRouter

from app.domains.user.router import login_router, user_router
from app.domains.item.router import router as item_router
from app.domains.blog.router import posts_router, categories_router, comments_router

router = APIRouter()

# 用户相关路由
router.include_router(login_router, tags=["login"])
router.include_router(user_router, prefix="/users", tags=["users"])

# 物品相关路由
router.include_router(item_router, prefix="/items", tags=["items"])

# Blog 路由
router.include_router(posts_router,      prefix="/blog/posts",      tags=["blog"])
router.include_router(categories_router, prefix="/blog/categories", tags=["blog"])
router.include_router(comments_router,   prefix="/blog",            tags=["blog"])
